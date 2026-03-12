import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950">
      {/* Navbar */}
      <nav className="border-b border-white/10 backdrop-blur-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
          <h1 className="text-xl font-bold text-white sm:text-2xl">
            Social<span className="text-purple-400">Genius</span>
          </h1>
          <div className="flex gap-2 sm:gap-3">
            <Link href="/login">
              <Button variant="ghost" className="text-white hover:text-purple-300 px-3 text-sm sm:px-4 sm:text-base">
                Iniciar Sesión
              </Button>
            </Link>
            <Link href="/register">
              <Button className="bg-purple-600 hover:bg-purple-700 px-3 text-sm sm:px-4 sm:text-base">
                Empezar Gratis
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="mx-auto max-w-7xl px-4 py-12 text-center sm:px-6 md:py-24">
        <h2 className="mx-auto max-w-4xl text-3xl font-bold leading-tight text-white sm:text-4xl md:text-5xl">
          Estrategias de contenido con{" "}
          <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            Inteligencia Artificial
          </span>
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-base text-slate-300 sm:mt-6 sm:text-lg">
          SocialGenius analiza tu negocio y genera calendarios editoriales,
          copywriting optimizado, hashtags relevantes y estrategias completas
          para Instagram y TikTok.
        </p>
        <div className="mt-8 flex justify-center gap-4 sm:mt-10">
          <Link href="/register">
            <Button size="lg" className="bg-purple-600 hover:bg-purple-700 px-6 text-base sm:px-8 sm:text-lg">
              Comenzar Gratis
            </Button>
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-7xl px-4 pb-12 sm:px-6 sm:pb-24">
        <div className="grid gap-4 sm:gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          <Card className="border-white/10 bg-white/5 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-white">Calendario Editorial</CardTitle>
            </CardHeader>
            <CardContent className="text-slate-300">
              Genera calendarios semanales completos con contenido listo para
              publicar, horarios óptimos y formatos específicos para cada
              plataforma.
            </CardContent>
          </Card>
          <Card className="border-white/10 bg-white/5 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-white">Copywriting con IA</CardTitle>
            </CardHeader>
            <CardContent className="text-slate-300">
              Captions optimizados, hooks que detienen el scroll, CTAs
              convincentes y variaciones para A/B testing, todo adaptado a tu
              industria.
            </CardContent>
          </Card>
          <Card className="border-white/10 bg-white/5 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-white">Hashtags y Tendencias</CardTitle>
            </CardHeader>
            <CardContent className="text-slate-300">
              Investigación de hashtags con sets pre-armados, tendencias de
              TikTok relevantes y estrategia personalizada para tu nicho.
            </CardContent>
          </Card>
          <Card className="border-white/10 bg-white/5 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-white">Análisis de Negocio</CardTitle>
            </CardHeader>
            <CardContent className="text-slate-300">
              La IA analiza tu industria, audiencia y competidores para crear
              estrategias personalizadas y pilares de contenido únicos.
            </CardContent>
          </Card>
          <Card className="border-white/10 bg-white/5 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-white">Instagram + TikTok</CardTitle>
            </CardHeader>
            <CardContent className="text-slate-300">
              Estrategias específicas: Reels, Carruseles, Stories, videos de
              TikTok, challenges y formatos trending.
            </CardContent>
          </Card>
          <Card className="border-white/10 bg-white/5 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-white">IA de Última Generación</CardTitle>
            </CardHeader>
            <CardContent className="text-slate-300">
              Potenciado por GPT-4o y Claude para contenido de la más alta
              calidad, adaptado a la voz de tu marca.
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Pricing */}
      <section className="mx-auto max-w-7xl px-4 pb-12 sm:px-6 sm:pb-24">
        <h3 className="mb-8 text-center text-2xl font-bold text-white sm:mb-12 sm:text-3xl">
          Planes
        </h3>
        <div className="mx-auto grid max-w-4xl gap-6 sm:gap-8 grid-cols-1 md:grid-cols-2">
          <Card className="border-white/10 bg-white/5 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-white">Gratis</CardTitle>
              <p className="text-3xl font-bold text-white">
                $0
                <span className="text-sm font-normal text-slate-400">/mes</span>
              </p>
            </CardHeader>
            <CardContent className="space-y-2 text-slate-300">
              <p>1 negocio</p>
              <p>3 estrategias/mes</p>
              <p>2 calendarios/mes</p>
              <p>50 mensajes/mes</p>
            </CardContent>
          </Card>
          <Card className="border-purple-500/50 bg-purple-950/30 backdrop-blur-sm ring-1 ring-purple-500/30">
            <CardHeader>
              <CardTitle className="text-white">Pro</CardTitle>
              <p className="text-3xl font-bold text-white">
                $29
                <span className="text-sm font-normal text-slate-400">/mes</span>
              </p>
            </CardHeader>
            <CardContent className="space-y-2 text-slate-300">
              <p>Negocios ilimitados</p>
              <p>Estrategias ilimitadas</p>
              <p>Calendarios ilimitados</p>
              <p>Mensajes ilimitados</p>
              <p>GPT-4o + Claude</p>
              <p>Exportar y editar</p>
            </CardContent>
          </Card>
        </div>
      </section>

      <footer className="border-t border-white/10 py-8 text-center text-slate-500">
        <p>SocialGenius AI - Estrategias de contenido potenciadas por IA</p>
      </footer>
    </div>
  );
}
