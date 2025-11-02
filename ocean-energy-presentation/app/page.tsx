"use client"

import { useState } from "react"

export default function OceanEnergyPresentation() {
  const [currentSlide, setCurrentSlide] = useState(0)

  const slides = [
    {
      id: 0,
      title: "Ocean Energy Production",
      subtitle: "Harnessing the Power of Our Seas",
      content: "Exploring sustainable energy solutions from the world's oceans",
      gradient: "from-blue-600 via-cyan-500 to-teal-400"
    },
    {
      id: 1,
      title: "What is Ocean Energy?",
      subtitle: "Renewable Power from the Sea",
      points: [
        "Energy derived from ocean waves, tides, currents, and thermal gradients",
        "Vast, predictable, and renewable resource",
        "Covers 71% of Earth's surface with enormous energy potential",
        "Estimated global potential: 20,000-80,000 TWh per year"
      ],
      gradient: "from-blue-500 via-blue-600 to-indigo-600"
    },
    {
      id: 2,
      title: "Types of Ocean Energy",
      subtitle: "Four Main Technologies",
      sections: [
        { name: "Tidal Energy", desc: "Harnesses gravitational pull of moon and sun" },
        { name: "Wave Energy", desc: "Captures kinetic energy from surface waves" },
        { name: "Ocean Thermal", desc: "Uses temperature differences in water layers" },
        { name: "Ocean Current", desc: "Extracts energy from continuous water flow" }
      ],
      gradient: "from-cyan-500 via-blue-500 to-purple-600"
    },
    {
      id: 3,
      title: "Tidal Energy",
      subtitle: "Predictable and Powerful",
      points: [
        "Uses rise and fall of tides to generate electricity",
        "Highly predictable - tides follow known patterns",
        "Tidal barrages and tidal stream generators",
        "Example: La Rance Tidal Power Station (France) - 240 MW capacity"
      ],
      gradient: "from-blue-600 via-indigo-600 to-purple-600"
    },
    {
      id: 4,
      title: "Wave Energy",
      subtitle: "Capturing Ocean Motion",
      points: [
        "Converts kinetic energy of ocean waves into electricity",
        "Various technologies: point absorbers, attenuators, oscillating water columns",
        "Abundant resource along coastlines worldwide",
        "Still in development phase with promising pilot projects"
      ],
      gradient: "from-cyan-600 via-blue-600 to-blue-700"
    },
    {
      id: 5,
      title: "Ocean Thermal Energy",
      subtitle: "Temperature Difference Power",
      points: [
        "OTEC systems use temperature difference between surface and deep water",
        "Requires minimum 20°C temperature difference",
        "Works best in tropical regions",
        "Can provide continuous baseload power 24/7"
      ],
      gradient: "from-orange-500 via-red-500 to-pink-600"
    },
    {
      id: 6,
      title: "Benefits of Ocean Energy",
      subtitle: "Why Invest in Ocean Power?",
      points: [
        "100% renewable and sustainable resource",
        "Predictable and reliable compared to wind/solar",
        "Minimal visual impact - mostly underwater",
        "High energy density - more power per square meter",
        "Reduces dependence on fossil fuels",
        "Creates jobs in coastal communities"
      ],
      gradient: "from-green-500 via-emerald-500 to-teal-600"
    },
    {
      id: 7,
      title: "Current Projects Worldwide",
      subtitle: "Leading the Way",
      sections: [
        { name: "MeyGen (Scotland)", desc: "World's largest tidal stream project - 6 MW" },
        { name: "Sihwa Lake (South Korea)", desc: "254 MW tidal power station" },
        { name: "WaveRoller (Portugal)", desc: "Innovative wave energy converter" },
        { name: "OTEC Plant (Hawaii)", desc: "Experimental thermal energy facility" }
      ],
      gradient: "from-blue-500 via-purple-500 to-pink-500"
    },
    {
      id: 8,
      title: "Environmental Considerations",
      subtitle: "Balancing Power and Nature",
      points: [
        "Minimal greenhouse gas emissions during operation",
        "Potential impacts on marine ecosystems require careful study",
        "Noise and electromagnetic fields may affect marine life",
        "Proper site selection and monitoring are essential",
        "Overall environmental footprint much lower than fossil fuels"
      ],
      gradient: "from-teal-600 via-green-600 to-emerald-600"
    },
    {
      id: 9,
      title: "Challenges Ahead",
      subtitle: "Obstacles to Overcome",
      points: [
        "High initial capital costs for infrastructure",
        "Harsh marine environment requires durable equipment",
        "Grid connection and energy storage challenges",
        "Limited commercial-scale deployment experience",
        "Need for supportive policies and regulations"
      ],
      gradient: "from-slate-600 via-gray-600 to-zinc-700"
    },
    {
      id: 10,
      title: "The Future of Ocean Energy",
      subtitle: "A Wave of Opportunity",
      points: [
        "Technology costs decreasing with innovation",
        "Growing global commitment to renewable energy",
        "Potential to power millions of coastal homes",
        "Integration with other renewable sources",
        "Key role in achieving net-zero emissions goals"
      ],
      gradient: "from-blue-600 via-cyan-500 to-emerald-500"
    },
    {
      id: 11,
      title: "Thank You",
      subtitle: "The Ocean's Power Awaits",
      content: "Together, we can harness the endless energy of our seas for a sustainable future",
      gradient: "from-indigo-600 via-blue-600 to-cyan-500"
    }
  ]

  const nextSlide = () => {
    if (currentSlide < slides.length - 1) {
      setCurrentSlide(currentSlide + 1)
    }
  }

  const prevSlide = () => {
    if (currentSlide > 0) {
      setCurrentSlide(currentSlide - 1)
    }
  }

  const goToSlide = (index: number) => {
    setCurrentSlide(index)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowRight") nextSlide()
    if (e.key === "ArrowLeft") prevSlide()
  }

  const slide = slides[currentSlide]

  return (
    <div 
      className="min-h-screen w-full flex flex-col items-center justify-center p-4 bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900"
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      {/* Main Slide Container */}
      <div className="w-full max-w-6xl h-[600px] relative">
        {/* Slide Content */}
        <div className={`w-full h-full rounded-2xl shadow-2xl bg-gradient-to-br ${slide.gradient} p-12 flex flex-col justify-center transition-all duration-500 ease-in-out`}>
          
          {/* Title Slide */}
          {(slide.id === 0 || slide.id === 11) && (
            <div className="text-center space-y-6">
              <h1 className="text-6xl md:text-7xl font-bold text-white mb-6 tracking-tight">
                {slide.title}
              </h1>
              <p className="text-2xl md:text-3xl text-white/90 font-light">
                {slide.subtitle}
              </p>
              {slide.content && (
                <p className="text-xl text-white/80 mt-8 max-w-3xl mx-auto">
                  {slide.content}
                </p>
              )}
            </div>
          )}

          {/* Content Slides with Points */}
          {slide.points && (
            <div className="space-y-8">
              <div className="space-y-2">
                <h2 className="text-5xl font-bold text-white tracking-tight">
                  {slide.title}
                </h2>
                <p className="text-2xl text-white/90 font-light">
                  {slide.subtitle}
                </p>
              </div>
              <ul className="space-y-4 mt-8">
                {slide.points.map((point, index) => (
                  <li 
                    key={index} 
                    className="text-xl text-white/95 flex items-start gap-4 animate-fade-in"
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    <span className="text-2xl mt-1 flex-shrink-0">•</span>
                    <span>{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Content Slides with Sections */}
          {slide.sections && (
            <div className="space-y-8">
              <div className="space-y-2">
                <h2 className="text-5xl font-bold text-white tracking-tight">
                  {slide.title}
                </h2>
                <p className="text-2xl text-white/90 font-light">
                  {slide.subtitle}
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
                {slide.sections.map((section, index) => (
                  <div 
                    key={index}
                    className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 hover:bg-white/20 transition-all duration-300"
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    <h3 className="text-2xl font-semibold text-white mb-2">
                      {section.name}
                    </h3>
                    <p className="text-lg text-white/90">
                      {section.desc}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Navigation Arrows */}
        <button
          onClick={prevSlide}
          disabled={currentSlide === 0}
          className="absolute left-4 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm border border-white/30 flex items-center justify-center text-white text-2xl hover:bg-white/30 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Previous slide"
        >
          ‹
        </button>
        <button
          onClick={nextSlide}
          disabled={currentSlide === slides.length - 1}
          className="absolute right-4 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm border border-white/30 flex items-center justify-center text-white text-2xl hover:bg-white/30 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Next slide"
        >
          ›
        </button>
      </div>

      {/* Slide Indicators */}
      <div className="flex gap-2 mt-8">
        {slides.map((_, index) => (
          <button
            key={index}
            onClick={() => goToSlide(index)}
            className={`h-2 rounded-full transition-all duration-300 ${
              index === currentSlide 
                ? "w-8 bg-white" 
                : "w-2 bg-white/40 hover:bg-white/60"
            }`}
            aria-label={`Go to slide ${index + 1}`}
          />
        ))}
      </div>

      {/* Slide Counter */}
      <div className="mt-4 text-white/70 text-sm">
        {currentSlide + 1} / {slides.length}
      </div>

      {/* Instructions */}
      <div className="mt-6 text-white/50 text-sm text-center">
        Use arrow keys or click buttons to navigate
      </div>
    </div>
  )
}
