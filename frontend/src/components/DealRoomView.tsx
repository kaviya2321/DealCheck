import React, { useState, useEffect, useRef, useCallback } from 'react';
import { DealData, ChatMessage, AIRiskUpdate, PayPalCard, User } from '../types';
import { createDealRoomSocket, getDealMessages, fetchDealById, agreeTerms, askDealCheckAi } from '../api';
import { RiskGauge } from './RiskGauge';
import { 
  ShieldCheck, ShieldAlert, AlertTriangle, Send, CheckCircle2, 
  ExternalLink, Sparkles, MessageSquare, Info, Lock, ChevronLeft,
  ChevronRight, RefreshCw, Zap, Copy, Check
} from 'lucide-react';

interface DealRoomViewProps {
  deal: DealData;
  currentUser: User;
  onDealUpdated: (deal: DealData) => void;
  onBack: () => void;
}

export function DealRoomView({ deal: initialDeal, currentUser, onDealUpdated, onBack }: DealRoomViewProps) {
  const [deal, setDeal] = useState<DealData>(initialDeal);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState<string | null>(null);
  const [aiRisk, setAiRisk] = useState<AIRiskUpdate | null>(null);
  const [paypalCard, setPaypalCard] = useState<PayPalCard | null>(
    initialDeal.paypal_order_id ? {
      order_id: initialDeal.paypal_order_id,
      approval_url: initialDeal.paypal_approval_url || '',
      amount: initialDeal.price,
      currency: initialDeal.currency,
      item_name: initialDeal.item_name,
      status: initialDeal.paypal_status || 'CREATED',
      sandbox_notice: 'Sandbox checkout, no real money.'
    } : null
  );
  const [isConnected, setIsConnected] = useState(false);
  const [aiQuestion, setAiQuestion] = useState('');
  const [aiAnswer, setAiAnswer] = useState<string | null>(null);
  const [isAskingAi, setIsAskingAi] = useState(false);
  const [showAiPanel, setShowAiPanel] = useState(true);
  const [copiedLink, setCopiedLink] = useState(false);
  const [typingTimeout, setTypingTimeout] = useState<ReturnType<typeof setTimeout> | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const isBuyer = deal.buyer_id === currentUser.id;
  const userRole = isBuyer ? 'buyer' : 'seller';

  // Load history on mount
  useEffect(() => {
    getDealMessages(deal.id).then(msgs => setMessages(msgs)).catch(console.warn);
  }, [deal.id]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Setup WebSocket
  useEffect(() => {
    const ws = createDealRoomSocket(deal.id);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    ws.onerror = () => setIsConnected(false);

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        handleWsEvent(payload.type, payload.data);
      } catch (e) {
        console.error('[WS] Parse error', e);
      }
    };

    return () => {
      ws.close();
    };
  }, [deal.id]);

  const handleWsEvent = useCallback((type: string, data: Record<string, unknown>) => {
    switch (type) {
      case 'connected':
        break;

      case 'chat_message':
        setMessages(prev => [...prev, {
          id: data.id as string,
          sender_id: data.sender_id as string,
          sender_name: data.sender_name as string,
          sender_role: data.sender_role as 'buyer' | 'seller',
          content: data.content as string,
          message_type: 'chat',
          created_at: data.created_at as string,
        }]);
        setIsTyping(null);
        break;

      case 'system_message':
        setMessages(prev => [...prev, {
          id: `sys_${Date.now()}`,
          sender_id: 'system',
          sender_name: 'DealCheck AI',
          sender_role: 'buyer',
          content: data.content as string,
          message_type: 'system',
          created_at: new Date().toISOString(),
        }]);
        break;

      case 'typing':
        if ((data.user_id as string) !== currentUser.id) {
          setIsTyping(data.is_typing ? (data.user_name as string) : null);
        }
        break;

      case 'ai_risk_update':
        setAiRisk(data as unknown as AIRiskUpdate);
        break;

      case 'paypal_card':
        setPaypalCard(data as unknown as PayPalCard);
        setMessages(prev => [...prev, {
          id: `pp_${Date.now()}`,
          sender_id: 'system',
          sender_name: 'DealCheck AI',
          sender_role: 'buyer',
          content: '__paypal_card__',
          message_type: 'paypal_card',
          created_at: new Date().toISOString(),
        }]);
        break;

      case 'agreement_updated':
        setDeal(prev => ({
          ...prev,
          buyer_agreed: data.buyer_agreed as boolean,
          seller_agreed: data.seller_agreed as boolean,
        }));
        break;

      case 'payment_captured':
        setPaypalCard(prev => prev ? { ...prev, status: data.status as string } : null);
        setDeal(prev => ({ ...prev, status: 'COMPLETED', paypal_status: data.status as string }));
        break;

      case 'presence_update':
        fetchDealById(deal.id).then(updated => {
          setDeal(updated);
          onDealUpdated(updated);
        }).catch(console.warn);
        break;
    }
  }, [currentUser.id, deal.id, onDealUpdated]);

  function sendMessage(textToSend?: string) {
    const text = (textToSend ?? inputText).trim();
    if (!text || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ type: 'chat_message', content: text }));
    if (!textToSend) setInputText('');
    sendTypingStop();
  }

  function sendTypingStart() {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'typing', is_typing: true }));
    }
  }

  function sendTypingStop() {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'typing', is_typing: false }));
    }
  }

  function handleInputChange(val: string) {
    setInputText(val);
    sendTypingStart();
    if (typingTimeout) clearTimeout(typingTimeout);
    setTypingTimeout(setTimeout(sendTypingStop, 2000));
  }

  async function handleAgree() {
    try {
      const updated = await agreeTerms(deal.id, true);
      setDeal(updated);
      onDealUpdated(updated);
    } catch (e) {
      console.error('Agree error', e);
    }
  }

  async function handleAskAi(e: React.FormEvent) {
    e.preventDefault();
    if (!aiQuestion.trim()) return;
    setIsAskingAi(true);
    setAiAnswer(null);
    try {
      const { answer } = await askDealCheckAi(deal.id, aiQuestion.trim());
      setAiAnswer(answer);
      setAiQuestion('');
    } catch (e) {
      setAiAnswer('DealCheck AI is temporarily unavailable. Use the risk gauge as your guide.');
    } finally {
      setIsAskingAi(false);
    }
  }

  const handleCopyInvite = () => {
    if (!deal.invite_token) return;
    const url = `${window.location.origin}/join/${deal.invite_token}`;
    navigator.clipboard.writeText(url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const riskScore = aiRisk?.risk_score ?? deal.risk_score;
  const verdict = aiRisk?.verdict ?? deal.verdict;

  return (
    <div className="flex flex-col lg:flex-row h-[calc(100vh-112px)] overflow-hidden bg-slate-50 dark:bg-slate-950">
      {/* ===== MAIN CHAT COLUMN ===== */}
      <div className="flex-1 flex flex-col min-w-0 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 shadow-sm">
        
        {/* Deal Header Bar */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <button 
              onClick={onBack} 
              className="p-1.5 text-slate-500 hover:text-slate-800 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
              title="Back to Deals List"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="font-extrabold text-base sm:text-lg text-slate-900 dark:text-white truncate">
                  {deal.item_name}
                </h2>
                <span className="font-bold text-sm px-2.5 py-0.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-700">
                  ${deal.price.toFixed(2)} {deal.currency}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                  deal.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300' :
                  deal.status === 'PAYMENT_PENDING' ? 'bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300' :
                  'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                }`}>
                  {deal.status}
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                <span>Role: <strong className="text-blue-600 dark:text-blue-400 capitalize">{userRole}</strong></span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-400'}`} />
                  {isConnected ? 'Live WebSocket' : 'Reconnecting…'}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Seller Invite Link button if seller hasn't joined */}
            {isBuyer && deal.invite_token && (
              <button
                onClick={handleCopyInvite}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors border border-slate-200 dark:border-slate-700"
                title="Copy seller invite link"
              >
                {copiedLink ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                <span className="hidden sm:inline">{copiedLink ? 'Link Copied!' : 'Share Invite'}</span>
              </button>
            )}

            {/* Mobile AI Panel Toggle */}
            {isBuyer && (
              <button
                onClick={() => setShowAiPanel(!showAiPanel)}
                className={`lg:hidden flex items-center gap-1 px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                  showAiPanel 
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-700'
                }`}
              >
                <Zap className="w-3.5 h-3.5" />
                <span>AI ({riskScore}/100)</span>
              </button>
            )}
          </div>
        </div>

        {/* Agreement Status Banner */}
        {deal.status === 'ACTIVE' && !paypalCard && (
          <div className="shrink-0 px-5 py-2.5 bg-gradient-to-r from-blue-50 via-indigo-50/50 to-blue-50 dark:from-blue-950/40 dark:via-indigo-950/30 dark:to-blue-950/40 border-b border-blue-200 dark:border-blue-800/60 flex items-center justify-between text-xs sm:text-sm">
            <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
              <Info className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0" />
              <span>
                {isBuyer
                  ? deal.buyer_agreed ? '✓ You agreed to the terms. Waiting for seller to confirm…' : 'Agree on price and item details in the chat, then click confirm.'
                  : deal.seller_agreed ? '✓ You agreed. Waiting for buyer to confirm…' : 'Once you and the buyer agree on terms, confirm below.'}
              </span>
            </div>
            {!(isBuyer ? deal.buyer_agreed : deal.seller_agreed) && (
              <button
                onClick={handleAgree}
                className="ml-3 px-3.5 py-1.5 text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-sm hover:shadow transition-all shrink-0"
              >
                Agree to Terms ✓
              </button>
            )}
          </div>
        )}

        {/* Messages Stream */}
        <div 
          className="flex-1 overflow-y-auto px-5 py-5 space-y-4"
          role="log"
          aria-live="polite"
          aria-label="Encrypted Deal Room Chat"
        >
          {/* Welcome Notice */}
          <div className="text-center py-6 px-4 max-w-md mx-auto">
            <div className="w-12 h-12 mx-auto rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white flex items-center justify-center shadow-md shadow-blue-500/20 mb-3">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-sm text-slate-800 dark:text-slate-100">Secured DealCheck Room</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
              DealCheck AI monitors this chat live to prevent fraud. When both parties agree on price, an authentic PayPal Goods & Services card is posted automatically.
            </p>
          </div>

          {messages.map((msg) => {
            const isMe = msg.sender_id === currentUser.id;
            const isSystem = msg.sender_id === 'system' || msg.message_type === 'system';
            const isPayPalCard = msg.message_type === 'paypal_card';

            // Render PayPal Card directly in the chat stream
            if (isPayPalCard && paypalCard) {
              return (
                <div key={msg.id} className="flex justify-center my-4">
                  <div className="max-w-md w-full bg-gradient-to-b from-white to-blue-50/30 dark:from-slate-800 dark:to-slate-800/80 rounded-2xl shadow-xl border-2 border-blue-500/40 dark:border-blue-500/50 p-5 overflow-hidden relative">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-full blur-2xl pointer-events-none" />
                    
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2.5">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#003087] to-[#0070BA] text-white flex items-center justify-center font-black text-sm shadow-md shadow-blue-600/30">
                          PP
                        </div>
                        <div>
                          <h4 className="font-extrabold text-sm text-slate-900 dark:text-white">PayPal Goods & Services</h4>
                          <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Full 180-Day Buyer Protection Active
                          </span>
                        </div>
                      </div>
                      <span className={`text-[11px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider ${
                        paypalCard.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300' :
                        paypalCard.status === 'CREATED' ? 'bg-blue-100 text-blue-800 dark:bg-blue-950/80 dark:text-blue-300' :
                        'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300'
                      }`}>
                        {paypalCard.status}
                      </span>
                    </div>

                    <div className="bg-white/80 dark:bg-slate-900/60 rounded-xl p-3.5 border border-slate-200/80 dark:border-slate-700/80 space-y-2 mb-4">
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-500 dark:text-slate-400">Item:</span>
                        <strong className="text-slate-800 dark:text-slate-100">{paypalCard.item_name}</strong>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-500 dark:text-slate-400">Protected Amount:</span>
                        <strong className="text-base text-slate-900 dark:text-white font-extrabold">
                          ${paypalCard.amount.toFixed(2)} {paypalCard.currency}
                        </strong>
                      </div>
                      <div className="flex justify-between text-[11px] text-slate-400 border-t border-slate-100 dark:border-slate-800 pt-1.5">
                        <span>PayPal Orders v2 ID:</span>
                        <code className="font-mono">{paypalCard.order_id.substring(0, 18)}…</code>
                      </div>
                    </div>

                    {paypalCard.status === 'CREATED' && isBuyer && (
                      <a
                        href={paypalCard.approval_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-full py-3 px-4 bg-gradient-to-r from-[#0070BA] to-[#003087] hover:from-[#005EA6] hover:to-[#00266B] text-white font-bold rounded-xl text-center shadow-lg shadow-blue-600/20 hover:shadow-blue-600/30 transition-all flex items-center justify-center gap-2 text-sm"
                      >
                        <span>Complete Sandbox Checkout</span>
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    )}

                    {paypalCard.status === 'COMPLETED' && (
                      <div className="py-2.5 px-4 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-xl text-center text-xs font-bold text-emerald-700 dark:text-emerald-300 flex items-center justify-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                        <span>Payment Successfully Approved & Captured!</span>
                      </div>
                    )}

                    <p className="text-[10px] text-center text-slate-400 dark:text-slate-500 mt-2.5">
                      🔒 Official PayPal Sandbox • No real currency charged
                    </p>
                  </div>
                </div>
              );
            }

            // System notifications
            if (isSystem) {
              return (
                <div key={msg.id} className="flex justify-center my-2">
                  <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/80 rounded-xl px-4 py-2.5 text-xs text-amber-800 dark:text-amber-200 max-w-lg text-center shadow-sm flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-amber-500 shrink-0" />
                    <span>{msg.content}</span>
                  </div>
                </div>
              );
            }

            // Normal Buyer/Seller chat bubbles
            return (
              <div key={msg.id} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[78%] sm:max-w-[70%] ${isMe ? 'items-end' : 'items-start'} flex flex-col`}>
                  {!isMe && (
                    <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1 ml-1 flex items-center gap-1">
                      <span>{msg.sender_name}</span>
                      <span className="text-[10px] uppercase font-bold text-slate-400">({msg.sender_role})</span>
                    </span>
                  )}
                  <div className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed shadow-sm ${
                    isMe
                      ? 'bg-blue-600 text-white rounded-br-xs font-normal'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 border border-slate-200/80 dark:border-slate-700/80 rounded-bl-xs'
                  }`}>
                    {msg.content}
                  </div>
                  <span className="text-[10px] text-slate-400 dark:text-slate-500 mt-1 px-1">
                    {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            );
          })}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl rounded-bl-xs px-4 py-2 text-xs text-slate-500 dark:text-slate-400 flex items-center gap-2">
                <span>{isTyping} is typing</span>
                <span className="inline-flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-bounce delay-0" />
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-bounce delay-150" />
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-bounce delay-300" />
                </span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Test Prompt Chips for Hackathon Demo */}
        <div className="px-5 py-2 bg-slate-50/60 dark:bg-slate-900/60 border-t border-slate-100 dark:border-slate-800 flex items-center gap-2 overflow-x-auto text-xs shrink-0">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 shrink-0">Quick Demo Prompts:</span>
          {userRole === 'seller' ? (
            <>
              <button
                onClick={() => sendMessage("Can you pay me via Friends and Family to save fees?")}
                className="px-2.5 py-1 rounded-lg bg-red-50 hover:bg-red-100 dark:bg-red-950/40 dark:hover:bg-red-900/40 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800 font-medium whitespace-nowrap transition-colors"
              >
                🚨 Test F&F Coercion
              </button>
              <button
                onClick={() => sendMessage("Sounds good! I agree with the price.")}
                className="px-2.5 py-1 rounded-lg bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-950/40 dark:hover:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 font-medium whitespace-nowrap transition-colors"
              >
                ✅ Agree on Price
              </button>
              <button
                onClick={() => sendMessage("No, I won't use goods and services. Send via Zelle.")}
                className="px-2.5 py-1 rounded-lg bg-red-50 hover:bg-red-100 dark:bg-red-950/40 dark:hover:bg-red-900/40 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800 font-medium whitespace-nowrap transition-colors"
              >
                ⛔ Test Refusal (Walk Away)
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => sendMessage("Hi, is the item still available in good condition?")}
                className="px-2.5 py-1 rounded-lg bg-slate-200/70 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-medium whitespace-nowrap transition-colors"
              >
                👋 Inquire Item
              </button>
              <button
                onClick={() => sendMessage("I can do that price. Please confirm the deal.")}
                className="px-2.5 py-1 rounded-lg bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/40 dark:hover:bg-blue-900/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 font-medium whitespace-nowrap transition-colors"
              >
                🤝 Agree to Deal
              </button>
            </>
          )}
        </div>

        {/* Message Input Box */}
        <div className="shrink-0 p-4 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <form 
            onSubmit={(e) => { e.preventDefault(); sendMessage(); }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={inputText}
              onChange={e => handleInputChange(e.target.value)}
              placeholder={`Type a message as ${userRole}… (Press Enter)`}
              className="flex-1 px-4 py-3 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white dark:focus:bg-slate-800 transition shadow-inner"
              disabled={!isConnected}
            />
            <button
              type="submit"
              disabled={!inputText.trim() || !isConnected}
              className="p-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-xl shadow-md shadow-blue-500/20 transition-all shrink-0 flex items-center justify-center"
              aria-label="Send message"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>
      </div>

      {/* ===== RIGHT COLUMN: Live AI Risk & Litmus Panel (Buyer Private) ===== */}
      {isBuyer && (
        <div className={`w-full lg:w-96 xl:w-[420px] flex flex-col border-t lg:border-t-0 lg:border-l border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 transition-all ${
          showAiPanel ? 'flex' : 'hidden lg:flex'
        }`}>
          {/* Header */}
          <div className="px-5 py-3.5 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shrink-0 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-slate-900 dark:text-white">DealCheck AI Co-Pilot</h3>
                <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">
                  🔒 Private to Buyer Only
                </span>
              </div>
            </div>
            <button 
              onClick={() => setShowAiPanel(false)}
              className="lg:hidden p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg"
            >
              ✕
            </button>
          </div>

          {/* Scrollable Risk Engine Content */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            
            {/* SVG Interactive Gauge */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-slate-200/80 dark:border-slate-800 shadow-soft">
              <RiskGauge score={riskScore} verdict={verdict} size={240} />
            </div>

            {/* Walk Away Litmus Banner */}
            {aiRisk?.refusal_warning && (
              <div className="bg-red-50 dark:bg-red-950/60 border-2 border-red-500 dark:border-red-600 rounded-2xl p-4 shadow-sm animate-pulse">
                <div className="flex items-center gap-2 text-red-700 dark:text-red-300 font-extrabold text-sm mb-1">
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                  <span>SELLER LITMUS TEST FAILED</span>
                </div>
                <p className="text-xs text-red-800 dark:text-red-200 leading-relaxed font-semibold">
                  {aiRisk.refusal_warning}
                </p>
              </div>
            )}

            {/* AI Guidance Box */}
            {(aiRisk?.guidance || deal.guidance) && !aiRisk?.refusal_warning && (
              <div className={`rounded-xl p-3.5 text-xs leading-relaxed border ${
                verdict === 'HIGH' ? 'bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-900 text-red-800 dark:text-red-200 font-medium' :
                verdict === 'MEDIUM' ? 'bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-900 text-amber-800 dark:text-amber-200' :
                'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-900 text-emerald-800 dark:text-emerald-200'
              }`}>
                <strong className="block mb-1 font-bold">Safety Assessment:</strong>
                {aiRisk?.guidance ?? deal.guidance}
              </div>
            )}

            {/* Highlighted Log-Odds Tokens */}
            {(aiRisk?.highlighted_phrases?.length ?? 0) > 0 && (
              <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-slate-200/80 dark:border-slate-800 shadow-soft">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2.5">
                  Risky Seller Phrases Flagged
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {aiRisk!.highlighted_phrases.map((hp, idx) => (
                    <span 
                      key={idx} 
                      className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-semibold ${
                        hp.weight > 0 
                          ? 'bg-red-100 text-red-800 dark:bg-red-950/70 dark:text-red-300 border border-red-200 dark:border-red-800'
                          : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/70 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
                      }`}
                      title={hp.reason}
                    >
                      "{hp.phrase}"
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Deterministic Rule Violations */}
            {(aiRisk?.rules_triggered?.length ?? deal.rules_triggered?.length ?? 0) > 0 && (
              <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-slate-200/80 dark:border-slate-800 shadow-soft">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
                  Active Rule Violations
                </h4>
                <div className="space-y-2">
                  {(aiRisk?.rules_triggered ?? deal.rules_triggered).map((rule) => (
                    <div key={rule.id} className="flex items-start gap-2 text-xs">
                      <span className="text-red-500 font-bold shrink-0">⚠</span>
                      <div>
                        <div className="font-bold text-slate-800 dark:text-slate-100">
                          {rule.name} <span className="text-red-600 dark:text-red-400">(+{rule.points} pts)</span>
                        </div>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">{rule.explanation}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Score Formula Breakdown */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-slate-200/80 dark:border-slate-800 shadow-soft text-xs">
              <h4 className="font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
                Transparent Risk Formula
              </h4>
              <div className="space-y-1.5 text-slate-600 dark:text-slate-400 font-mono">
                <div className="flex justify-between">
                  <span>Model A (TF-IDF + LR):</span>
                  <span className="text-slate-900 dark:text-white font-bold">+{aiRisk?.model_base_points ?? deal.model_base_points ?? 0} pts</span>
                </div>
                <div className="flex justify-between">
                  <span>Deterministic Rules:</span>
                  <span className="text-red-600 dark:text-red-400 font-bold">+{aiRisk?.rule_points_total ?? deal.rule_points_total ?? 0} pts</span>
                </div>
                <div className="flex justify-between border-t border-slate-100 dark:border-slate-800 pt-1.5 mt-1 font-bold text-sm text-slate-900 dark:text-white">
                  <span>Composite Score:</span>
                  <span>{riskScore} / 100</span>
                </div>
              </div>
            </div>

            {/* "Ask DealCheck AI" Interactive Drawer */}
            <div className="bg-gradient-to-b from-blue-50/50 to-white dark:from-slate-900 dark:to-slate-900 rounded-2xl p-4 border border-blue-200/80 dark:border-blue-900/60 shadow-soft space-y-3">
              <div className="flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <h4 className="font-bold text-xs text-blue-900 dark:text-blue-300 uppercase tracking-wider">
                  Ask DealCheck AI Advisor
                </h4>
              </div>
              <form onSubmit={handleAskAi} className="flex gap-2">
                <input
                  type="text"
                  value={aiQuestion}
                  onChange={e => setAiQuestion(e.target.value)}
                  placeholder="e.g. Is it safe if seller asks for deposit?"
                  className="flex-1 px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="submit"
                  disabled={isAskingAi || !aiQuestion.trim()}
                  className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white text-xs font-bold rounded-xl transition-all"
                >
                  Ask
                </button>
              </form>
              {isAskingAi && (
                <p className="text-xs text-blue-600 dark:text-blue-400 animate-pulse font-medium">
                  Consulting safety engine…
                </p>
              )}
              {aiAnswer && (
                <div className="p-3 bg-blue-50 dark:bg-blue-950/60 rounded-xl text-xs text-blue-900 dark:text-blue-200 border border-blue-200/60 dark:border-blue-800 leading-relaxed">
                  {aiAnswer}
                </div>
              )}
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
