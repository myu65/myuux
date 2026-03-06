import { Conversation } from "../lib/api";

type Props = {
  conversations: Conversation[];
  selectedConversationId: string | null;
  loading: boolean;
  newConversationTitle: string;
  onNewConversationTitleChange: (value: string) => void;
  onCreateConversation: (event: React.FormEvent<HTMLFormElement>) => void;
  onSelectConversation: (conversationId: string) => void;
};

export function ConversationSidebar(props: Props) {
  return (
    <section className="border rounded-lg p-3 bg-white col-span-3 space-y-3">
      <h2 className="font-bold">Conversations</h2>
      <form onSubmit={props.onCreateConversation} className="flex gap-2">
        <input
          value={props.newConversationTitle}
          onChange={(event) => props.onNewConversationTitleChange(event.target.value)}
          className="border rounded px-2 py-1 text-sm w-full"
          placeholder="new conversation"
        />
        <button className="bg-slate-800 text-white rounded px-3 py-1 text-sm" type="submit">
          Add
        </button>
      </form>
      <div className="text-xs text-slate-500">{props.loading ? "Loading..." : `${props.conversations.length} conversation(s)`}</div>
      <ul className="space-y-2 text-sm">
        {props.conversations.map((conversation) => (
          <li key={conversation.id}>
            <button
              className={`w-full text-left rounded px-2 py-1 ${
                conversation.id === props.selectedConversationId ? "bg-slate-200" : "hover:bg-slate-50"
              }`}
              onClick={() => props.onSelectConversation(conversation.id)}
            >
              {conversation.title}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
