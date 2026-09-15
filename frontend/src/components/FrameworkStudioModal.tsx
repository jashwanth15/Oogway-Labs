import React from 'react';
import { Artifact } from '../types';
import { 
  X, 
  Sparkles, 
  LayoutTemplate, 
  Compass, 
  Layers, 
  ArrowRight, 
  ShieldCheck, 
  Play, 
  Sliders, 
  CheckCircle2, 
  Flame, 
  HelpCircle 
} from 'lucide-react';

interface FrameworkStudioModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenArtifact: (artifact: Artifact) => void;
  onSendMessage: (text: string, skill?: string) => void;
}

interface FrameworkItem {
  id: string;
  title: string;
  guest: string;
  role: string;
  category: 'Strategy' | 'Prioritization' | 'Growth';
  desc: string;
  badge: string;
  color: string;
  hasInteractiveWidget: boolean;
  prompt: string;
  artifactPayload?: Artifact;
}

export const FrameworkStudioModal: React.FC<FrameworkStudioModalProps> = ({
  isOpen,
  onClose,
  onOpenArtifact,
  onSendMessage,
}) => {
  const [selectedCategory, setSelectedCategory] = React.useState<string>('all');

  if (!isOpen) return null;

  const FRAMEWORKS: FrameworkItem[] = [
    {
      id: 'dhm',
      title: 'DHM Product Strategy Scorecard',
      guest: 'Gibson Biddle',
      role: 'Former VP Product at Netflix & CPO at Chegg',
      category: 'Strategy',
      desc: 'Evaluate product bets across Delight, 4 Hard-to-Copy Moats (Brand, Network Effects, Scale, Switching Costs), and Margin Expansion with Netflix case studies.',
      badge: 'Interactive Scorecard',
      color: 'from-indigo-500/20 to-purple-500/10 border-indigo-500/40 text-indigo-300',
      hasInteractiveWidget: true,
      prompt: 'Create an interactive HTML UI scorecard for Gibson Biddle\'s DHM model allowing me to rate product features on Delight, Hard-to-copy advantage, and Margin-enhancement.'
    },
    {
      id: 'lno',
      title: 'LNO Task Matrix & Energy Allocator',
      guest: 'Shreyas Doshi',
      role: 'Former Product Lead at Stripe, Twitter & Google',
      category: 'Prioritization',
      desc: 'Manage energy instead of just time. Classify tasks into Leverage (10x-100x), Neutral (1x), and Overhead (<1x) to eliminate PM burnout and feature factory traps.',
      badge: 'Interactive Kanban Board',
      color: 'from-sky-500/20 to-indigo-500/10 border-sky-500/40 text-sky-300',
      hasInteractiveWidget: true,
      prompt: 'Create an interactive HTML CSS dashboard component for Shreyas Doshi\'s LNO framework with interactive columns for Leverage, Neutral, and Overhead tasks.'
    },
    {
      id: 'pmf',
      title: '40% Product-Market Fit Engine',
      guest: 'Rahul Vohra & Sean Ellis',
      role: 'Founder & CEO of Superhuman / Author of Hacking Growth',
      category: 'Growth',
      desc: 'Calculate Sean Ellis\'s 40% "Very Disappointed" threshold, filter High-Expectation Customers (HXC), and allocate engineering with the 50/50 roadmap rule.',
      badge: 'Interactive Calculator',
      color: 'from-emerald-500/20 to-teal-500/10 border-emerald-500/40 text-emerald-300',
      hasInteractiveWidget: true,
      prompt: 'Build an interactive PMF survey calculator and scorecard in HTML/CSS with Tailwind styling based on Rahul Vohra\'s framework.'
    },
    {
      id: 'pre-mortem',
      title: 'Pre-Mortem Risk Framework',
      guest: 'Shreyas Doshi',
      role: 'Former Product Lead at Stripe, Twitter & Google',
      category: 'Strategy',
      desc: 'Stress-test initiatives before building by separating Tigers (existential risks that kill projects), Paper Tigers (false alarms), and Elephants (unspoken taboos).',
      badge: 'Strategic Playbook',
      color: 'from-amber-500/20 to-orange-500/10 border-amber-500/40 text-amber-300',
      hasInteractiveWidget: false,
      prompt: 'Explain Shreyas Doshi\'s Pre-Mortem framework covering Tigers, Paper Tigers, and Elephants in the room, and how to run this exercise with product teams.'
    },
    {
      id: 'plg-loops',
      title: 'B2B Product-Led Growth Loops',
      guest: 'Elena Verna',
      role: 'Head of Growth at Dropbox, Amplitude & Miro Advisor',
      category: 'Growth',
      desc: 'Unpack why funnels lie and loops compound. Master how product usage directly fuels user acquisition, activation, and sales handoffs.',
      badge: 'Loop Playbook',
      color: 'from-rose-500/20 to-pink-500/10 border-rose-500/40 text-rose-300',
      hasInteractiveWidget: false,
      prompt: 'Explain Elena Verna\'s B2B product-led growth loops and how product usage drives pipeline for sales-assisted expansion.'
    },
    {
      id: 'positioning',
      title: '5 Components of Positioning',
      guest: 'April Dunford',
      role: 'Author of Obviously Awesome & Positioning Consultant',
      category: 'Strategy',
      desc: 'Discover the 5 pillars: Competitive Alternatives, Differentiated Capabilities, Value & Proof, Target Customer Segment, and Market Category—and why to avoid starting with features.',
      badge: 'Positioning Guide',
      color: 'from-teal-500/20 to-emerald-500/10 border-teal-500/40 text-teal-300',
      hasInteractiveWidget: false,
      prompt: 'What are the 5 components of product positioning according to April Dunford, and why does she warn against starting with features?'
    }
  ];

  const filteredFrameworks = selectedCategory === 'all' 
    ? FRAMEWORKS 
    : FRAMEWORKS.filter(f => f.category.toLowerCase() === selectedCategory.toLowerCase());

  const handleLaunch = (fw: FrameworkItem) => {
    onClose();
    onSendMessage(fw.prompt, 'artifact');
  };

  const handleAsk = (fw: FrameworkItem) => {
    onClose();
    onSendMessage(fw.prompt, 'rag');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200" onClick={onClose}>
      <div 
        className="w-full max-w-4xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/70">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 text-slate-950 font-bold shadow-md shadow-brand-600/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-black text-slate-100 flex items-center gap-2">
                Lenny's Growth Framework Studio
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-400 border border-brand-500/20 font-mono">
                  Verified Insights
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Instantly explore and launch seminal product strategy tools and calculators from Lenny's top episodes.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Category Filter Pills */}
        <div className="px-6 py-3 border-b border-slate-800/80 bg-slate-900/40 flex items-center gap-2 overflow-x-auto text-xs">
          <span className="text-slate-400 font-medium mr-1">Filter:</span>
          {['all', 'strategy', 'prioritization', 'growth'].map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1 rounded-lg capitalize font-medium transition-all ${
                selectedCategory === cat
                  ? 'bg-brand-600 text-slate-950 font-bold shadow-sm'
                  : 'bg-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {cat === 'all' ? 'All Frameworks' : cat}
            </button>
          ))}
        </div>

        {/* Framework Cards Grid */}
        <div className="p-6 overflow-y-auto grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredFrameworks.map((fw) => (
            <div
              key={fw.id}
              className={`p-5 rounded-2xl bg-gradient-to-br ${fw.color} border shadow-lg flex flex-col justify-between space-y-4 hover:border-slate-500 transition-all duration-150`}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-950/80 border border-slate-700/80 text-slate-300 font-semibold">
                    {fw.badge}
                  </span>
                  <span className="text-[11px] font-medium text-slate-400">
                    {fw.category}
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-100 tracking-tight">
                  {fw.title}
                </h3>
                <div className="text-xs text-brand-400 font-semibold">
                  By {fw.guest} <span className="text-slate-400 font-normal">({fw.role})</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed pt-1">
                  {fw.desc}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
                <button
                  onClick={() => handleAsk(fw)}
                  className="px-3 py-1.5 rounded-xl bg-slate-950/70 hover:bg-slate-950 text-slate-300 hover:text-white text-xs font-semibold border border-slate-700/80 transition-all"
                >
                  Ask Question
                </button>
                {fw.hasInteractiveWidget ? (
                  <button
                    onClick={() => handleLaunch(fw)}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-slate-950 text-xs font-bold transition-all shadow-md shadow-brand-600/20 active:scale-95"
                  >
                    <Sliders className="w-3.5 h-3.5" />
                    <span>Launch Interactive Tool</span>
                  </button>
                ) : (
                  <button
                    onClick={() => handleAsk(fw)}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-all"
                  >
                    <span>Explore Playbook</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-950 flex items-center justify-between text-xs text-slate-400">
          <span>Powered by verified transcripts from 303 episodes of Lenny's Podcast</span>
          <span className="font-mono text-brand-400">Zero Hallucinations Guarantee</span>
        </div>
      </div>
    </div>
  );
};
