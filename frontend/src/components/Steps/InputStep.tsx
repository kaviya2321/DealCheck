import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, Image as ImageIcon, Sparkles, AlertTriangle, ArrowRight, Loader2, FileText, CheckCircle2 } from 'lucide-react';
import { extractChat, analyzeDeal } from '../../api';
import { DealData } from '../../types';

interface InputStepProps {
  onDealAnalyzed: (deal: DealData) => void;
  isLoading: boolean;
  setIsLoading: (val: boolean) => void;
}

const SAMPLE_SCAM_CHAT = `Buyer: Hi Alex, is the PlayStation 5 still available for $320?
Seller: Yes still available! Need it gone quickly. Are you ready to pay right now?
Buyer: Yes, I can take it. Can I pay via PayPal Goods and Services so we both have protection?
Seller: No sorry, I only accept PayPal Friends and Family. PayPal business takes a big fee and holds my money for 21 days. Send through Friends & Family only.
Buyer: But Goods and Services protects me if the console doesn't arrive or is broken.
Seller: Bro I have 100% positive reviews on my profile. If you want it, pay by Friends and Family now or I will sell to someone else waiting.`;

const SAMPLE_LEGIT_CHAT = `Buyer: Hi Sarah, is the Sony Alpha A7 IV Camera still available?
Seller: Yes, it's available! In great shape, shutter count is only 4,200. Comes with original charger and box.
Buyer: Awesome. Can we meet in person to test it before buying?
Seller: Absolutely. How about we meet at Whole Foods lobby tomorrow around 2 PM? You can inspect and test everything thoroughly.
Buyer: That sounds perfect. How would you like payment?
Seller: Cash in person or PayPal Goods and Services when you're satisfied with the condition.`;

export const InputStep: React.FC<InputStepProps> = ({
  onDealAnalyzed,
  isLoading,
  setIsLoading,
}) => {
  const [chatText, setChatText] = useState('');
  const [itemName, setItemName] = useState('PlayStation 5 Disc Edition');
  const [price, setPrice] = useState<number | string>(320);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isExtractingImage, setIsExtractingImage] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle clipboard paste of image
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;

      for (let i = 0; i < items.length; i++) {
        if (items[i].type.startsWith('image/')) {
          const file = items[i].getAsFile();
          if (file) {
            handleFileSelect(file);
            break;
          }
        }
      }
    };
    window.addEventListener('paste', handlePaste);
    return () => window.removeEventListener('paste', handlePaste);
  }, []);

  const handleFileSelect = async (file: File) => {
    setSelectedFile(file);
    setErrorMsg(null);

    // Create memory preview
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);

    // Call extraction
    setIsExtractingImage(true);
    try {
      const extracted = await extractChat({ file });
      if (extracted.chat_text) setChatText(extracted.chat_text);
      if (extracted.item_name && extracted.item_name !== 'Marketplace Item') setItemName(extracted.item_name);
      if (extracted.price && extracted.price > 0) setPrice(extracted.price);
    } catch (err: any) {
      setErrorMsg(err.message || 'Vision OCR failed. Please paste text directly.');
    } finally {
      setIsExtractingImage(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleRunAnalysis = async () => {
    if (!chatText.trim()) {
      setErrorMsg('Please paste conversation text or upload a screenshot to analyze.');
      return;
    }

    setErrorMsg(null);
    setIsLoading(true);

    try {
      const numPrice = typeof price === 'string' ? parseFloat(price) || 0 : price;
      const deal = await analyzeDeal({
        chat_text: chatText,
        item_name: itemName || 'Marketplace Item',
        price: numPrice,
        currency: 'USD',
        source_type: selectedFile ? 'screenshot' : 'text_paste',
      });
      onDealAnalyzed(deal);
    } catch (err: any) {
      setErrorMsg(err.message || 'DealCheck analysis failed. Please retry.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Intro Header */}
      <div className="text-center space-y-2">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Step 1: Check Any Marketplace Deal
        </h1>
        <p className="text-sm text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
          Paste the negotiation chat from Facebook Marketplace, OLX, or Instagram, or drop a screenshot.
          Our trained AI model instantly scores transaction safety.
        </p>
      </div>

      {/* Sample Chat Fillers */}
      <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Try sample chats:</span>
        <button
          type="button"
          onClick={() => {
            setChatText(SAMPLE_SCAM_CHAT);
            setItemName('PlayStation 5 Disc Edition');
            setPrice(320);
            setSelectedFile(null);
            setPreviewUrl(null);
            setErrorMsg(null);
          }}
          className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-300 border border-red-200 dark:border-red-900 hover:bg-red-100 transition-colors"
        >
          🚨 Typical Scam (F&F Coercion)
        </button>

        <button
          type="button"
          onClick={() => {
            setChatText(SAMPLE_LEGIT_CHAT);
            setItemName('Sony Alpha A7 IV Camera');
            setPrice(1200);
            setSelectedFile(null);
            setPreviewUrl(null);
            setErrorMsg(null);
          }}
          className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900 hover:bg-emerald-100 transition-colors"
        >
          ✅ Legitimate Deal (In-Person & G&S)
        </button>
      </div>

      {/* Error Banner with Retry and Quick-Fix */}
      {errorMsg && (
        <div className="p-4 bg-red-50 dark:bg-red-950/70 border border-red-200 dark:border-red-800 rounded-xl text-red-800 dark:text-red-200 text-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-sm">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 text-red-600 mt-0.5" />
            <div>
              <p className="font-bold">Check Notice</p>
              <p className="mt-0.5 text-xs opacity-90">{errorMsg}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2 flex-shrink-0 self-end sm:self-center">
            <button
              type="button"
              onClick={() => {
                setChatText(SAMPLE_SCAM_CHAT);
                setItemName('PlayStation 5 Disc Edition');
                setPrice(320);
                setErrorMsg(null);
              }}
              className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-bold transition-colors shadow-sm"
            >
              Fill Sample Text
            </button>
            <button
              type="button"
              onClick={handleRunAnalysis}
              className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-bold transition-colors shadow-sm"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Main Form Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Drag & Drop Zone + Image Preview */}
        <div className="md:col-span-1 space-y-4">
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-paypal-blue dark:hover:border-paypal-blue rounded-2xl p-6 text-center cursor-pointer bg-white dark:bg-slate-900/60 transition-all flex flex-col items-center justify-center min-h-[200px]"
          >
            <input
              type="file"
              ref={fileInputRef}
              accept="image/*"
              className="hidden"
              onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
            />

            {isExtractingImage ? (
              <div className="space-y-2 flex flex-col items-center">
                <Loader2 className="w-8 h-8 text-paypal-blue animate-spin" />
                <p className="text-xs font-bold text-slate-700 dark:text-slate-300">Extracting text from screenshot...</p>
                <p className="text-[10px] text-slate-400">Processed in-memory only</p>
              </div>
            ) : previewUrl ? (
              <div className="space-y-2 flex flex-col items-center">
                <img
                  src={previewUrl}
                  alt="Screenshot preview"
                  className="max-h-32 object-contain rounded-lg shadow-sm border border-slate-200 dark:border-slate-800"
                />
                <span className="text-[11px] text-paypal-blue font-bold">Change Image</span>
                {chatText.length > 0 && (
                  <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800 flex items-center space-x-1">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>Transcribed to conversation</span>
                  </span>
                )}
              </div>
            ) : (
              <div className="space-y-2 flex flex-col items-center">
                <div className="w-12 h-12 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500">
                  <UploadCloud className="w-6 h-6 text-paypal-blue" />
                </div>
                <div className="text-xs font-bold text-slate-800 dark:text-slate-200">
                  Drop Screenshot or Paste (Ctrl+V)
                </div>
                <p className="text-[11px] text-slate-400">
                  PNG, JPG, or WebP. Auto-extracts chat & price in memory.
                </p>
              </div>
            )}
          </div>

          {/* Item Name & Price Inputs */}
          <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-soft space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">Deal Parameters</h3>
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Item Being Purchased
              </label>
              <input
                type="text"
                value={itemName}
                onChange={(e) => setItemName(e.target.value)}
                placeholder="e.g. iPhone 15 Pro, PS5"
                className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-paypal-blue focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Agreed Price ($ USD)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="320.00"
                className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-paypal-blue focus:outline-none"
              />
            </div>
          </div>
        </div>

        {/* Right Column: Chat Textarea + Analyze CTA */}
        <div className="md:col-span-2 space-y-4 flex flex-col justify-between">
          <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-soft flex-1 flex flex-col">
            <div className="flex flex-wrap items-center justify-between gap-1 mb-2">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Buyer-Seller Conversation Transcript
              </label>
              <div className="flex items-center space-x-1.5">
                {chatText.length > 0 && (
                  <>
                    <button
                      type="button"
                      onClick={() => {
                        const swapped = chatText
                          .replace(/^Buyer:/gmi, 'TEMP_ROLE:')
                          .replace(/^Seller:/gmi, 'Buyer:')
                          .replace(/^TEMP_ROLE:/gmi, 'Seller:');
                        setChatText(swapped);
                      }}
                      className="px-2 py-0.5 text-[11px] font-semibold text-paypal-deep dark:text-blue-300 bg-blue-50 dark:bg-blue-950/60 rounded border border-blue-200 dark:border-blue-900 hover:bg-blue-100 transition-colors"
                      title="Swap Buyer and Seller speaker roles"
                    >
                      ⇄ Swap Roles
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        const cleaned = chatText
                          .split('\n')
                          .filter(l => !l.match(/^\s*(buyer|seller)?\s*:?\s*\d{1,2}:\d{2}/i) && !l.match(/^\s*(buyer|seller)?\s*:?\s*(OFF|ON|Active|Online|Seen|Delivered|v['\/]*)\s*$/i))
                          .join('\n');
                        setChatText(cleaned);
                      }}
                      className="px-2 py-0.5 text-[11px] font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700 hover:bg-slate-200 transition-colors"
                      title="Remove timestamps and noise"
                    >
                      Clean Noise
                    </button>
                  </>
                )}
                <span className="text-[11px] text-slate-400">
                  {chatText.length} chars
                </span>
              </div>
            </div>
            <textarea
              rows={11}
              value={chatText}
              onChange={(e) => setChatText(e.target.value)}
              placeholder="Paste the marketplace negotiation transcript here, e.g.:&#10;Buyer: Can I pay with PayPal Goods and Services?&#10;Seller: No, my account is personal only. Send via Friends and Family..."
              className="w-full flex-1 p-3 text-sm bg-slate-50 dark:bg-slate-800/80 border border-slate-300 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-paypal-blue focus:outline-none font-mono text-slate-800 dark:text-slate-200 leading-relaxed resize-y"
            />
          </div>

          {/* Primary Action Button */}
          <button
            type="button"
            disabled={isLoading || !chatText.trim()}
            onClick={handleRunAnalysis}
            className="w-full py-4 px-6 rounded-2xl bg-gradient-to-r from-paypal-deep via-paypal-blue to-blue-600 hover:from-blue-900 hover:to-paypal-deep text-white font-extrabold text-base shadow-soft-lg flex items-center justify-center space-x-2 transition-all transform active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Running DealCheck Machine Learning Pipeline...</span>
              </>
            ) : (
              <>
                <span>Analyze Deal Safety with Our Model</span>
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
