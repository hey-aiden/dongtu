import client from './client';

// 无登录体系,用 localStorage 持久化一个随机 user_id,保证会话归属稳定
const USER_KEY = 'dongtu_user_id';

function getUserId() {
  let id = localStorage.getItem(USER_KEY);
  if (!id) {
    id = `u-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
    localStorage.setItem(USER_KEY, id);
  }
  return id;
}

// 后端角色 human/ai ↔ 前端 user/assistant
export const ROLE_TO_FRONT = { human: 'user', ai: 'assistant' };

// 创建会话
export function createConversation(title) {
  return client.post('/ai-chat/conversation_create', {
    user_id: getUserId(),
    title,
  });
}

// 会话列表
export function listConversations(page = 1, pageSize = 50) {
  return client.get('/ai-chat/conversation_list', {
    params: { user_id: getUserId(), page, page_size: pageSize },
  });
}

// 发送消息,返回 AI 回复 { content, role }
export function sendMessage(conversationId, content) {
  return client.post('/ai-chat/message_insert', {
    conversation_id: conversationId,
    content,
  });
}

// 历史消息(后端按时间倒序返回,前端需反转为正序)
export function listMessages(conversationId, page = 1, pageSize = 100) {
  return client.get('/ai-chat/message_history_list', {
    params: { conversation_id: conversationId, page, page_size: pageSize },
  });
}
