"use client"

import { useState } from 'react'

export default function Home() {
  const [currentSlide, setCurrentSlide] = useState(0)

  const slides = [
    {
      id: 0,
      title: "Ocean Energy Production",
      subtitle: "Harnessing the Power of Our Seas",
      content: "Exploring sustainable energy solutions from the world's oceans"
    },
    {
      id: 1,
      title: "What is Ocean Energy?",
      subtitle: "Renewable Power from the Sea",
      content: "Ocean energy refers to renewable energy derived from ocean waves, tides, currents, temperature differences, and salinity gradients. It represents one of the most promising sources of clean, sustainable power for our future."
    },
    {
      id: 2,
      title: "Types of Ocean Energy",
      subtitle: "Four Main Technologies",
      points: [
        { name: "Tidal Energy", desc: "Harnesses the gravitational pull of the moon and sun on ocean tides" },
        { name: "Wave Energy", desc: "Captures energy from surface waves created by wind" },
        { name: "Ocean Thermal Energy", desc: "Uses temperature differences between surface and deep water" },
        { name: "Ocean Current Energy", desc: "Extracts kinetic energy from continuous ocean currents" }
      ]
    },
    {
      id: 3,
      title: "Tidal Energy",
      subtitle: "Predictable and Powerful",
      content: "Tidal energy is one of the most reliable forms of renewable energy. Tides are highly predictable, occurring twice daily with consistent patterns. Tidal barrages and tidal stream generators convert the kinetic energy of moving water into electricity.",
      stats: [
        { label: "Predictability", value: "100%" },
        { label: "Global Potential", value: "800 TWh/year" }
      ]
    },
    {
      id: 4,
      title: "Wave Energy",
      subtitle: "Capturing Ocean Motion",
      content: "Wave energy converters capture the energy from ocean surface waves. Various technologies exist, including point absorbers, attenuators, and oscillating water columns. Waves contain tremendous energy density, making them an attractive renewable resource.",
      stats: [
        { label: "Energy Density", value: "2-3 kW/m²" },
        { label: "Global Potential", value: "29,500 TWh/year" }
      ]
    },
    {
      id: 5,
      title: "Benefits of Ocean Energy",
      subtitle: "Why Ocean Power Matters",
      points: [
        { name: "Renewable & Sustainable", desc: "Inexhaustible energy source with no fuel costs" },
        { name: "Zero Emissions", desc: "No greenhouse gases or air pollutants during operation" },
        { name: "High Energy Density", desc: "Water is 800x denser than air, providing concentrated power" },
        { name: "Predictable Output", desc: "Tides and currents follow reliable patterns" },
        { name: "Minimal Land Use", desc: "Offshore installations preserve valuable land resources" }
      ]
    },
    {
      id: 6,
      title: "Current Projects Worldwide",
      subtitle: "Leading the Blue Revolution",
      content: "Ocean energy projects are operational or under development across the globe. Notable installations include the MeyGen tidal array in Scotland, the Sihwa Lake Tidal Power Station in South Korea, and wave energy test sites in Portugal and Australia.",
      regions: [
        { name: "Europe", status: "Leading in tidal stream technology" },
        { name: "Asia", status: "Largest tidal barrage installations" },
        { name: "North America", status: "Growing wave energy research" },
        { name: "Oceania", status: "Extensive testing facilities" }
      ]
    },
    {
      id: 7,
      title: "Environmental Impact",
      subtitle: "Balancing Power and Nature",
      content: "While ocean energy is clean and renewable, careful consideration must be given to marine ecosystems. Modern installations are designed to minimize impacts on marine life, with ongoing research into fish-friendly turbines and habitat enhancement.",
      considerations: [
        "Marine life protection measures",
        "Minimal visual and noise impact",
        "Potential for artificial reef creation",
        "Continuous environmental monitoring"
      ]
    },
    {
      id: 8,
      title: "Challenges & Solutions",
      subtitle: "Overcoming Obstacles",
      points: [
        { name: "High Initial Costs", desc: "Decreasing through technology advancement and scale" },
        { name: "Harsh Marine Environment", desc: "Developing corrosion-resistant materials and designs" },
        { name: "Grid Connection", desc: "Improving offshore transmission infrastructure" },
        { name: "Environmental Concerns", desc: "Implementing eco-friendly designs and monitoring" }
      ]
    },
    {
      id: 9,
      title: "The Future of Ocean Energy",
      subtitle: "A Wave of Opportunity",
      content: "Ocean energy has the potential to provide up to 10% of global electricity needs by 2050. With continued investment in research, development, and deployment, ocean energy will play a crucial role in the transition to a sustainable energy future.",
      projections: [
        "Projected capacity: 337 GW by 2050",
        "Cost reduction: 50-70% by 2030",
        "Job creation: 680,000 jobs globally",
        "CO₂ reduction: 500+ million tons annually"
      ]
    },
    {
      id: 10,
      title: "Thank You",
      subtitle: "The Future is Blue",
      content: "Ocean energy represents a vast, untapped resource that can help power our world sustainably. Together, we can harness the power of our seas for a cleaner, brighter future."
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

  const slide = slides[currentSlide]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-cyan-900 flex flex-col">
      {/* Main Slide Content */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-6xl">
          <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-2xl p-12 md:p-16 min-h-[500px] flex flex-col justify-center transition-all duration-500">
            {/* Slide Title */}
            <div className="mb-8">
              <h1 className="text-4xl md:text-6xl font-bold text-blue-900 mb-4">
                {slide.title}
              </h1>
              <h2 className="text-2xl md:text-3xl text-cyan-700 font-light">
                {slide.subtitle}
              </h2>
            </div>

            {/* Slide Content */}
            <div className="text-gray-700 text-lg md:text-xl leading-relaxed">
              {slide.content && (
                <p className="mb-6">{slide.content}</p>
              )}

              {slide.points && (
                <div className="space-y-4">
                  {slide.points.map((point, index) => (
                    <div key={index} className="border-l-4 border-cyan-500 pl-6 py-2">
                      <h3 className="font-bold text-blue-900 text-xl mb-1">{point.name}</h3>
                      <p className="text-gray-600">{point.desc}</p>
                    </div>
                  ))}
                </div>
              )}

              {slide.stats && (
                <div className="grid grid-cols-2 gap-6 mt-6">
                  {slide.stats.map((stat, index) => (
                    <div key={index} className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-6 text-center">
                      <div className="text-4xl font-bold text-blue-900 mb-2">{stat.value}</div>
                      <div className="text-gray-600 font-medium">{stat.label}</div>
                    </div>
                  ))}
                </div>
              )}

              {slide.regions && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                  {slide.regions.map((region, index) => (
                    <div key={index} className="bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg p-4">
                      <h3 className="font-bold text-blue-900 mb-1">{region.name}</h3>
                      <p className="text-gray-600 text-base">{region.status}</p>
                    </div>
                  ))}
                </div>
              )}

              {slide.considerations && (
                <ul className="space-y-3 mt-4">
                  {slide.considerations.map((item, index) => (
                    <li key={index} className="flex items-start">
                      <span className="text-cyan-500 mr-3 text-2xl">•</span>
                      <span className="text-gray-700">{item}</span>
                    </li>
                  ))}
                </ul>
              )}

              {slide.projections && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                  {slide.projections.map((proj, index) => (
                    <div key={index} className="bg-gradient-to-br from-cyan-50 to-blue-50 rounded-lg p-4 border-l-4 border-cyan-500">
                      <p className="text-gray-700 font-medium">{proj}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Controls */}
      <div className="bg-blue-950/50 backdrop-blur-sm py-6 px-8">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          {/* Previous Button */}
          <button
            onClick={prevSlide}
            disabled={currentSlide === 0}
            className={`px-6 py-3 rounded-lg font-semibold transition-all ${
              currentSlide === 0
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-cyan-500 text-white hover:bg-cyan-600 hover:scale-105'
            }`}
          >
            Previous
          </button>

          {/* Slide Indicators */}
          <div className="flex items-center gap-2">
            {slides.map((_, index) => (
              <button
                key={index}
                onClick={() => goToSlide(index)}
                className={`transition-all rounded-full ${
                  index === currentSlide
                    ? 'w-12 h-3 bg-cyan-400'
                    : 'w-3 h-3 bg-blue-300/50 hover:bg-blue-300'
                }`}
                aria-label={`Go to slide ${index + 1}`}
              />
            ))}
          </div>

          {/* Next Button */}
          <button
            onClick={nextSlide}
            disabled={currentSlide === slides.length - 1}
            className={`px-6 py-3 rounded-lg font-semibold transition-all ${
              currentSlide === slides.length - 1
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-cyan-500 text-white hover:bg-cyan-600 hover:scale-105'
            }`}
          >
            Next
          </button>
        </div>

        {/* Slide Counter */}
        <div className="text-center mt-4 text-cyan-200 text-sm">
          Slide {currentSlide + 1} of {slides.length}
        </div>
      </div>
    </div>
  )
}
