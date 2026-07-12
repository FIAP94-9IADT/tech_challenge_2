import { ChevronDown, MessageCircle, SendHorizonal, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { askQuestion } from "../services/api";

const SUGGESTIONS = [
  "Qual veículo tem a rota mais longa?",
  "Quantas entregas críticas temos hoje e em quais rotas?",
  "Algum veículo está perto do limite de capacidade?",
];

export default function ChatBox({ enabled, optimizationKey }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [unread, setUnread] = useState(0);
  const messagesEndRef = useRef(null);

  // nova otimização -> nova conversa (o contexto mudou)
  useEffect(() => {
    setMessages([]);
    setUnread(0);
  }, [optimizationKey]);

  // rola automaticamente até a última mensagem
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, open]);

  // abrir a janela zera o contador de não lidas
  useEffect(() => {
    if (open) setUnread(0);
  }, [open]);

  const send = async (text) => {
    const question = (text || input).trim();
    if (!question || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: question }]);
    setLoading(true);
    try {
      const { answer } = await askQuestion(question);
      setMessages((m) => [...m, { role: "assistant", text: answer }]);
      if (!open) setUnread((u) => u + 1);
    } catch (err) {
      setMessages((m) => [...m, { role: "assistant", text: `⚠️ ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-widget">
      {open && (
        <div className="chat-window">
          <button className="chat-window-header" onClick={() => setOpen(false)}>
            <span className="chat-avatar">
              <Sparkles size={15} />
            </span>
            <span className="chat-window-title">
              <strong>Assistente de rotas</strong>
              <small>{enabled ? "online · contexto da otimização atual" : "aguardando otimização"}</small>
            </span>
            <ChevronDown size={18} />
          </button>

          <div className="chat-messages">
            {!enabled && (
              <div className="chat-msg assistant">
                Otimize as rotas primeiro para conversar sobre elas. 😉
              </div>
            )}
            {enabled && messages.length === 0 && (
              <div className="chat-msg assistant">
                Oi! Posso responder perguntas sobre as rotas otimizadas. Tenta uma
                das sugestões abaixo ou escreve a sua.
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`chat-msg ${msg.role}`}>
                <ReactMarkdown>{msg.text}</ReactMarkdown>
              </div>
            ))}
            {loading && <div className="chat-msg assistant muted">Digitando...</div>}
            <div ref={messagesEndRef} />
          </div>

          {enabled && messages.length === 0 && (
            <div className="chat-suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s} className="btn btn-secondary btn-sm" onClick={() => send(s)}>
                  {s}
                </button>
              ))}
            </div>
          )}

          <div className="chat-input">
            <input
              className="form-control"
              value={input}
              disabled={!enabled || loading}
              placeholder="Ex.: qual a carga total da Van 2?"
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              autoFocus
            />
            <button
              className="btn btn-primary"
              disabled={!enabled || loading}
              onClick={() => send()}
              aria-label="Enviar"
            >
              <SendHorizonal size={15} />
            </button>
          </div>
        </div>
      )}

      {!open && (
        <div className="chat-fab-row">
          <button className="chat-fab-label" onClick={() => setOpen(true)}>
            {enabled
              ? "Dúvidas sobre as rotas? Pergunte aqui 👋"
              : "Precisa de ajuda? Fale com o assistente 👋"}
          </button>
          <button className="chat-fab" onClick={() => setOpen(true)} aria-label="Abrir chat">
            <MessageCircle size={24} />
            {unread > 0 && <span className="chat-fab-badge">{unread}</span>}
          </button>
        </div>
      )}
    </div>
  );
}
