import BehaviourMap from "@/components/BehaviourMap";
import Footer from "@/components/Footer";
import Hero from "@/components/Hero";
import Leaderboard from "@/components/Leaderboard";
import LiveTracker from "@/components/LiveTracker";
import TrendChart from "@/components/TrendChart";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-[1280px] space-y-16 px-6 py-12 md:px-10">
      <Hero />
      <section id="demo" className="scroll-mt-24">
        <LiveTracker />
      </section>
      <TrendChart />
      <BehaviourMap />
      <Leaderboard />
      <Footer />
    </main>
  );
}
