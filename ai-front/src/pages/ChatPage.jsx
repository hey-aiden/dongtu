import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  MODALITIES,
  DEFAULT_MODALITY_ID,
  INITIAL_CONVERSATIONS,
  createEmptyConversation,
  createMessage,
  PLACEHOLDER_REPLY,
} from '../data/modalities';
import {
  createConversation,
  listConversations,
  sendMessage,
  listMessages,
  ROLE_TO_FRONT,
} from '../api/chat';
import ModalityTabs from '../components/ModalityTabs';
import ConversationSidebar from '../components/ConversationSidebar';
import MessageList from '../components/MessageList';
import MessageInput from '../components/MessageInput';
import './ChatPage.css';

// 每个模态默认选中的会话(取各自第一条)。text 初始为空,后续由后端填充。
function buildInitialActive() {
  const map = {};
  for (const [modalityId, { conversations }] of Object.entries(INITIAL_CONVERSATIONS)) {
    map[modalityId] = conversations[0]?.id ?? null;
  }
  return map;
}

const truncateTitle = (text) => (text.length > 18 ? `${text.slice(0, 18)}…` : text);

export default function ChatPage() {
  const { modalityId } = useParams();

  // 模态由 URL 驱动;非法/缺失时回退到第一个
  const activeModality = MODALITIES.some((m) => m.id === modalityId)
    ? modalityId
    : DEFAULT_MODALITY_ID;
  const isText = activeModality === 'text';

  // 按模态分桶的会话数据;当前选中会话每个模态各自记住
  const [conversationsByModality, setConversationsByModality] = useState(INITIAL_CONVERSATIONS);
  const [activeByModality, setActiveByModality] = useState(buildInitialActive);

  // text 模态的异步状态
  const [sending, setSending] = useState(false);
  const [loadingList, setLoadingList] = useState(false);
  const [error, setError] = useState('');
  // 记录已拉取过历史的会话,避免重复请求与空会话死循环
  const loadedIdsRef = useRef(new Set());

  const conversations = conversationsByModality[activeModality].conversations;
  const activeConversationId = activeByModality[activeModality];
  const activeConversation = conversations.find((c) => c.id === activeConversationId);

  const updateConversations = (updater) => {
    setConversationsByModality((prev) => ({
      ...prev,
      [activeModality]: { conversations: updater(prev[activeModality].conversations) },
    }));
  };
  const setActive = (id) => {
    setActiveByModality((prev) => ({ ...prev, [activeModality]: id }));
  };

  // 进入 text 模态时加载会话列表
  useEffect(() => {
    if (!isText) return;
    let cancelled = false;
    setLoadingList(true);
    setError('');
    listConversations()
      .then((data) => {
        if (cancelled) return;
        const items = (data.items || []).map((c) => ({
          id: c.conversation_id,
          title: c.title,
          createdAt: c.created_at || null,
          messages: [],
        }));
        setConversationsByModality((prev) => ({ ...prev, text: { conversations: items } }));
        setActiveByModality((prev) => ({ ...prev, text: items[0]?.id ?? null }));
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoadingList(false));
    return () => {
      cancelled = true;
    };
  }, [isText]);

  // 选中会话后加载历史消息(text 模态);新建的空会话已在创建时标记,跳过拉取
  useEffect(() => {
    if (!isText || !activeConversationId) return;
    if (loadedIdsRef.current.has(activeConversationId)) return;
    loadedIdsRef.current.add(activeConversationId);
    let cancelled = false;
    setError('');
    listMessages(activeConversationId)
      .then((data) => {
        if (cancelled) return;
        const items = (data.items || [])
          .slice()
          .reverse()
          .map((m, i) => ({
            id: `h-${activeConversationId}-${i}`,
            role: ROLE_TO_FRONT[m.role] || m.role,
            content: m.content,
            type: 'text',
            createdAt: m.created_at,
          }));
        updateConversations((list) =>
          list.map((c) => (c.id === activeConversationId ? { ...c, messages: items } : c)),
        );
      })
      .catch((e) => {
        if (cancelled) return;
        loadedIdsRef.current.delete(activeConversationId); // 失败可重试
        setError(e.message);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeConversationId, isText]);

  const handleSelect = (id) => {
    setActive(id);
  };

  const handleCreate = async () => {
    if (!isText) {
      const conv = createEmptyConversation();
      updateConversations((list) => [conv, ...list]);
      setActive(conv.id);
      return;
    }
    try {
      setError('');
      const conv = await createConversation('新对话');
      loadedIdsRef.current.add(conv.conversation_id); // 新会话历史为空,无需拉取
      updateConversations((list) => [
        { id: conv.conversation_id, title: conv.title, createdAt: null, messages: [] },
        ...list,
      ]);
      setActive(conv.conversation_id);
    } catch (e) {
      setError(e.message);
    }
  };

  const handleSend = async (text) => {
    // 非文本模态维持原有 mock 行为
    if (!isText) {
      let convId = activeConversationId;
      if (!convId) {
        const conv = createEmptyConversation();
        convId = conv.id;
        updateConversations((list) => [conv, ...list]);
        setActive(conv.id);
      }
      const userMsg = createMessage('user', text, activeModality);
      const reply = createMessage('assistant', PLACEHOLDER_REPLY[activeModality], activeModality);
      updateConversations((list) =>
        list.map((c) => {
          if (c.id !== convId) return c;
          const title = c.messages.length === 0 ? truncateTitle(text) : c.title;
          return { ...c, title, messages: [...c.messages, userMsg, reply] };
        }),
      );
      return;
    }

    const derivedTitle = truncateTitle(text);
    let convId = activeConversationId;
    try {
      // 无会话时先建会话(首条消息作标题),再发送
      if (!convId) {
        const conv = await createConversation(derivedTitle);
        convId = conv.conversation_id;
        loadedIdsRef.current.add(convId);
        updateConversations((list) => [
          { id: convId, title: conv.title, createdAt: null, messages: [] },
          ...list,
        ]);
        setActive(convId);
      }

      // 乐观追加用户消息 + 进入发送中状态
      const userMsg = createMessage('user', text, 'text');
      updateConversations((list) =>
        list.map((c) => {
          if (c.id !== convId) return c;
          const title = c.messages.length === 0 ? derivedTitle : c.title;
          return { ...c, title, messages: [...c.messages, userMsg] };
        }),
      );
      setSending(true);
      setError('');

      const reply = await sendMessage(convId, text);
      const aiMsg = createMessage('assistant', reply.content, 'text');
      updateConversations((list) =>
        list.map((c) => (c.id === convId ? { ...c, messages: [...c.messages, aiMsg] } : c)),
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="chat-page">
      <header className="chat-header">
        <span className="chat-header__brand">AI Lab</span>
        <ModalityTabs activeId={activeModality} />
      </header>

      <div className="chat-body">
        <ConversationSidebar
          conversations={conversations}
          activeId={activeConversationId}
          loading={isText && loadingList}
          onSelect={handleSelect}
          onCreate={handleCreate}
        />

        <main className="chat-main">
          <MessageList
            messages={activeConversation?.messages ?? []}
            sending={sending}
            loading={isText && loadingList}
          />
          {error && <div className="chat-error">{error}</div>}
          <MessageInput onSend={handleSend} disabled={sending} />
        </main>
      </div>
    </div>
  );
}
