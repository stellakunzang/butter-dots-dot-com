import Image from 'next/image'

export const DictionaryEntry = () => {
  return (
    <div className="max-w-5xl mx-auto py-12">
      {/* Header */}
      <div className="mb-12 pb-6 border-b-2 border-gray-200">
        <div className="flex items-baseline gap-4 mb-2">
          <h1 className="text-6xl md:text-7xl font-serif text-gray-900 tracking-tight">
            butter dots
          </h1>
          <span className="text-2xl text-gray-400 font-light italic">
            /ˈbʌtər dɑts/
          </span>
        </div>
        <p className="text-lg text-gray-500 italic mt-2">noun, plural</p>
      </div>

      {/* Main Content Grid */}
      <div className="grid md:grid-cols-2 gap-12 mb-12">
        {/* Definition Section */}
        <div className="space-y-6">
          <div>
            <p className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Definition
            </p>
            <p className="text-xl leading-relaxed text-gray-800">
              Small discs of butter formed in ice cold water by rolling bits of
              butter (preferably european) into a ball and then pressing them
              flat.
            </p>
          </div>

          <div>
            <p className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Usage Notes
            </p>
            <ul className="space-y-2 text-base text-gray-600">
              <li className="flex gap-2">
                <span className="text-gray-400">•</span>
                <span>
                  European-style butter produces optimal results due to higher
                  fat content
                </span>
              </li>
              <li className="flex gap-2">
                <span className="text-gray-400">•</span>
                <span>
                  Ice water is essential to maintain butter consistency during
                  formation
                </span>
              </li>
              <li className="flex gap-2">
                <span className="text-gray-400">•</span>
                <span>Used to decorate torma offerings</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Image Section */}
        <div className="relative">
          <div className="sticky top-24">
            <Image
              src="/butterdots.jpg"
              alt="butter dots in a metal bowl with ice"
              width={600}
              height={800}
              priority
              className="rounded-lg shadow-xl w-full h-auto border border-gray-200"
            />
            <p className="text-sm text-gray-500 italic mt-3 text-center">
              Fig. 1: Butter dots prepared in ice water
            </p>
          </div>
        </div>
      </div>

    </div>
  )
}
