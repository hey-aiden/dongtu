// 中央消息历史。展示当前会话的全部消息,区分 user / assistant。
// sending:正在等待 AI 回复(显示加载气泡);loading:首次加载会话列表。
export default function MessageList({ messages, sending = false, loading = false }) {
  if (loading) {
    return (
      <div className="message-list message-list--empty">
        <p className="message-list__hint">加载中…</p>
      </div>
    );
  }

  if (messages.length === 0 && !sending) {
    return (
      <div className="message-list message-list--empty">
        <p className="message-list__hint">开始一段新对话吧</p>
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.map((m) => (
        <div key={m.id} className={`message message--${m.role}`}>
          <div className="message__role" aria-hidden="true">
            {m.role === 'user' ? '你' : 'AI'}
          </div>
          <div className="message__bubble">{m.content}</div>
        </div>
      ))}
      {sending && (
        <div className="message message--assistant">
          <div className="message__role" aria-hidden="true">
            AI
          </div>
          <div className="message__bubble message__bubble--pending">思考中…</div>
        </div>
      )}
    </div>
  );
}
