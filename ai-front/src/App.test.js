import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from './App';

// ChatPage 挂载即拉取会话列表,测试环境无后端,统一 mock 掉网络层
jest.mock('./api/chat', () => ({
  ROLE_TO_FRONT: { human: 'user', ai: 'assistant' },
  createConversation: async () => ({ conversation_id: 'c1', title: '新对话' }),
  listConversations: async () => ({ total: 0, items: [] }),
  sendMessage: async () => ({ content: 'hi', role: 'ai' }),
  listMessages: async () => ({ total: 0, items: [] }),
}));

test('renders chat page with modality tabs', async () => {
  render(
    <MemoryRouter initialEntries={['/chat/text']}>
      <App />
    </MemoryRouter>
  );
  await waitFor(() => {
    expect(screen.getByText(/文本对话/i)).toBeInTheDocument();
  });
  expect(screen.getByText(/文生图/i)).toBeInTheDocument();
  expect(screen.getByText(/语音/i)).toBeInTheDocument();
});
