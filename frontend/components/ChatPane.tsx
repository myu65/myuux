import { Conversation, ConversationDetail } from "../lib/api";

type Props = {
  selectedConversation: Conversation | undefined;
  detail: ConversationDetail | null;
  messageText: string;
  onMessageTextChange: (value: string) => void;
  onSendMessage: (event: React.FormEvent<HTMLFormElement>) => void;
  onRegenerate: (messageId: string) => void;
  onBranch: (messageId: string) => void;
};

export function ChatPane(props: Props) {
  return (
    <section className="border rounded-lg p-3 bg-white col-span-6 space-y-3">
      <h2 className="font-bold">Chat</h2>
      <p className="text-sm text-slate-600">{props.selectedConversation ? props.selectedConversation.title : "会話を選択"}</p>
      <ul className="space-y-2 text-sm max-h-[70vh] overflow-y-auto">
        {props.detail?.selected_path_messages.map((message) => (
          <li key={message.id} className="border rounded p-2 bg-slate-50">
            <div className="font-semibold text-xs uppercase text-slate-500">{message.role}</div>
            <div>{message.text}</div>
            {message.role === "user" ? (
              <button className="text-xs text-blue-700 mt-2 mr-2" onClick={() => props.onRegenerate(message.id)} type="button">
                regenerate
              </button>
            ) : null}
            <button className="text-xs text-purple-700 mt-2" onClick={() => props.onBranch(message.id)} type="button">
              branch from here
            </button>
          </li>
        ))}
      </ul>
      <form onSubmit={props.onSendMessage} className="space-y-2">
        <textarea
          value={props.messageText}
          onChange={(event) => props.onMessageTextChange(event.target.value)}
          className="border rounded px-2 py-1 text-sm w-full h-28"
        />
        <button className="bg-blue-700 text-white rounded px-3 py-1 text-sm w-full" type="submit">
          Send
        </button>
      </form>
    </section>
  );
}
