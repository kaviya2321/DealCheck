import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { HistoryView } from './components/HistoryView';
import { ModelCardView } from './components/ModelCardView';
import { AuthModal } from './components/AuthModal';
import { NewDealModal } from './components/NewDealModal';
import { DealRoomView } from './components/DealRoomView';
import { MyDealsList } from './components/MyDealsList';
import { DealData, User, HealthStatus } from './types';
import { fetchHealth, getMe, logout, getInvitePreview, joinDeal, fetchDealById } from './api';
import { ShieldCheck, MessageSquare, ShieldAlert, CreditCard, Lock, ArrowRight, Zap, CheckCircle2 } from 'lucide-react';

type MainTab = 'deals' | 'history' | 'model';

export function App() {
  // Auth state
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<'login' | 'signup'>('login');
  const [authPrefillMsg, setAuthPrefillMsg] = useState<string | undefined>(undefined);

  // Navigation state - Default to Deal Rooms
  const [currentTab, setCurrentTab] = useState<MainTab>('deals');
  const [activeDealRoom, setActiveDealRoom] = useState<DealData | null>(null);

  // Health & UI
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [showNewDealModal, setShowNewDealModal] = useState(false);
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  // Sync dark mode class
  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);

  // Fetch health
  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(err => console.warn('Health check error:', err));
  }, []);

  // Restore auth session on load
  useEffect(() => {
    getMe()
      .then(user => setCurrentUser(user))
      .catch(() => setCurrentUser(null))
      .finally(() => setAuthLoading(false));
  }, []);

  // Handle /join/TOKEN deep-link on page load
  useEffect(() => {
    const path = window.location.pathname;
    const joinMatch = path.match(/^\/join\/(.+)$/);
    if (joinMatch) {
      const token = joinMatch[1];
      handleInviteLink(token);
    }
  }, []);

  async function handleInviteLink(token: string) {
    try {
      const preview = await getInvitePreview(token);
      if (!currentUser) {
        setAuthPrefillMsg(`${preview.buyer_name} invited you to buy "${preview.item_name}" for $${preview.price.toFixed(2)} safely using DealCheck. Sign in or create an account to join the deal room.`);
        setAuthModalMode('signup');
        setShowAuthModal(true);
        sessionStorage.setItem('pendingInviteToken', token);
      } else {
        await completeJoin(token);
      }
    } catch (e) {
      console.warn('Invite preview error:', e);
    }
  }

  async function completeJoin(token: string) {
    try {
      const { deal_id } = await joinDeal(token);
      const dealData = await fetchDealById(deal_id);
      setActiveDealRoom(dealData);
      setCurrentTab('deals');
      window.history.replaceState({}, '', '/');
    } catch (e) {
      console.error('Join failed:', e);
    }
  }

  function handleAuthenticated(user: User, token: string) {
    setCurrentUser(user);
    setShowAuthModal(false);
    const pendingToken = sessionStorage.getItem('pendingInviteToken');
    if (pendingToken) {
      sessionStorage.removeItem('pendingInviteToken');
      completeJoin(pendingToken);
    }
  }

  async function handleLogout() {
    await logout();
    setCurrentUser(null);
    setActiveDealRoom(null);
    setCurrentTab('deals');
  }

  function handleSelectHistoricalDeal(selected: DealData) {
    setActiveDealRoom(selected);
    setCurrentTab('deals');
  }

  function handleNewDealClick() {
    if (!currentUser) {
      setAuthModalMode('signup');
      setAuthPrefillMsg('Create a free account or sign in to start a protected Deal Room.');
      setShowAuthModal(true);
    } else {
      setShowNewDealModal(true);
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <svg className="animate-spin w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-200">
      {/* Auth Modal */}
      {showAuthModal && (
        <AuthModal
          onClose={() => setShowAuthModal(false)}
          onAuthenticated={handleAuthenticated}
          initialMode={authModalMode}
          prefillMessage={authPrefillMsg}
        />
      )}

      {/* New Deal Modal */}
      {showNewDealModal && currentUser && (
        <NewDealModal
          onClose={() => setShowNewDealModal(false)}
          onDealCreated={(newDeal) => {
            setShowNewDealModal(false);
            setActiveDealRoom(newDeal);
            setCurrentTab('deals');
          }}
        />
      )}

      {/* Top Navbar */}
      <Navbar
        currentTab={currentTab}
        setCurrentTab={(tab) => setCurrentTab(tab as MainTab)}
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        health={health}
        currentUser={currentUser}
        onLogin={() => { setAuthModalMode('login'); setAuthPrefillMsg(undefined); setShowAuthModal(true); }}
        onLogout={handleLogout}
        onNewDeal={handleNewDealClick}
      />

      {/* Main Content View */}
      {currentTab === 'deals' && activeDealRoom && currentUser ? (
        <div className="flex-1 overflow-hidden">
          <DealRoomView
            deal={activeDealRoom}
            currentUser={currentUser}
            onDealUpdated={(updated) => setActiveDealRoom(updated)}
            onBack={() => setActiveDealRoom(null)}
          />
        </div>
      ) : (
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          {currentTab === 'deals' && (
            currentUser ? (
              <MyDealsList
                currentUser={currentUser}
                onSelectDeal={(d) => setActiveDealRoom(d)}
                onNewDeal={() => setShowNewDealModal(true)}
              />
            ) : (
              /* Public / Guest Hero Landing for Deal Rooms */
              <div className="max-w-4xl mx-auto py-8 sm:py-12">
                <div className="text-center space-y-4 mb-12">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-semibold">
                    <Zap className="w-3.5 h-3.5" />
                    <span>Real-Time Buyer Protection • No Copy-Pasting Required</span>
                  </div>
                  <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-slate-900 dark:text-white">
                    Close Marketplace Deals Safely with <span className="text-blue-600 dark:text-blue-400">DealCheck AI</span>
                  </h1>
                  <p className="max-w-2xl mx-auto text-base sm:text-lg text-slate-600 dark:text-slate-400 leading-relaxed">
                    Create a secured deal room, invite the seller, and negotiate live. DealCheck AI scores scam risks in real-time and automatically generates official PayPal Goods & Services protection.
                  </p>
                  <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-4">
                    <button
                      onClick={handleNewDealClick}
                      className="w-full sm:w-auto px-6 py-3.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30 transition-all flex items-center justify-center gap-2"
                    >
                      <span>Create a Protected Deal</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => { setAuthModalMode('login'); setShowAuthModal(true); }}
                      className="w-full sm:w-auto px-6 py-3.5 border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold rounded-xl transition-all"
                    >
                      Sign In to Your Deals
                    </button>
                  </div>
                </div>

                {/* 4-Step Collaborative Workflow Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 mb-12">
                  <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                      <MessageSquare className="w-5 h-5" />
                    </div>
                    <h3 className="text-base font-bold text-slate-900 dark:text-white">1. Live Collaborative Room</h3>
                    <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                      Buyer and seller chat directly inside DealCheck. All messages are encrypted at rest with private 48-hour invite links.
                    </p>
                  </div>

                  <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
                    <div className="w-10 h-10 rounded-xl bg-amber-100 dark:bg-amber-900/40 text-amber-600 dark:text-amber-400 flex items-center justify-center">
                      <ShieldAlert className="w-5 h-5" />
                    </div>
                    <h3 className="text-base font-bold text-slate-900 dark:text-white">2. Real-Time Scam Scoring</h3>
                    <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                      Our in-house trained ScamRiskModel scores each seller message. High-risk indicators (Friends & Family, Zelle, deposits) alert the buyer privately.
                    </p>
                  </div>

                  <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
                    <div className="w-10 h-10 rounded-xl bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400 flex items-center justify-center">
                      <CreditCard className="w-5 h-5" />
                    </div>
                    <h3 className="text-base font-bold text-slate-900 dark:text-white">3. Auto PayPal Protected Checkout</h3>
                    <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                      Once terms are agreed, DealCheck automatically creates and posts a genuine PayPal Goods & Services card with 180-day buyer protection.
                    </p>
                  </div>

                  <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
                    <div className="w-10 h-10 rounded-xl bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400 flex items-center justify-center">
                      <Lock className="w-5 h-5" />
                    </div>
                    <h3 className="text-base font-bold text-slate-900 dark:text-white">4. Model B Seller Litmus Test</h3>
                    <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                      If the seller refuses protected payment or pushes for off-platform rails, risk surges to 95/100: "Walk away: real sellers have no reason to refuse buyer protection."
                    </p>
                  </div>
                </div>

                {/* Honest Cryptography & Privacy Banner */}
                <div className="bg-slate-100 dark:bg-slate-900/60 rounded-xl p-4 border border-slate-200 dark:border-slate-800 text-xs text-slate-500 dark:text-slate-400 flex items-start gap-3">
                  <Lock className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-slate-700 dark:text-slate-300">Honest Security Disclosure:</strong> Chat messages are encrypted in transit (TLS/WSS) and encrypted at rest (Fernet AES-128). They are <em>not end-to-end encrypted</em> because DealCheck AI must inspect content on the server to protect you from scams. You retain full control to delete your deal data at any time.
                  </div>
                </div>
              </div>
            )
          )}

          {currentTab === 'history' && (
            <HistoryView
              onSelectDeal={handleSelectHistoricalDeal}
              onNewCheck={handleNewDealClick}
            />
          )}

          {currentTab === 'model' && <ModelCardView />}
        </main>
      )}

      {/* Footer — hidden when inside active Deal Room */}
      {!(currentTab === 'deals' && activeDealRoom) && (
        <footer className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 py-6 text-center text-xs text-slate-500 transition-colors">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-blue-600 dark:text-blue-400">DealCheck</span>
              <span>• Built for PayPal AI Hackathon</span>
            </div>
            <div>
              <span>Local TF-IDF + LR Models • AES-128 at Rest • Real PayPal Sandbox Orders v2</span>
            </div>
          </div>
        </footer>
      )}
    </div>
  );
}

export default App;
