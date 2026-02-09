import type {NextPage} from 'next'
import Image from 'next/image'
import {Layout, Button} from '../components'

const Home: NextPage = () => {
  return (
    <Layout
      title="Butter Dots"
      description="Butter Dots are small discs of butter formed in ice cold water"
    >
      <div className="flex flex-col items-center justify-center py-8 text-center max-w-4xl mx-auto">
        <h1 className="text-6xl font-serif text-gray-800 mb-2">
          Butter Dots Dot Com
        </h1>
        <p className="text-xl text-gray-400 italic mb-1">
          (try saying it out loud...fun!)
        </p>
        <p className="text-xl text-gray-400 italic mb-12">
          (yes, Jon, I fixed the typo)
        </p>

        <div className="my-12 max-w-2xl w-full">
          <Image
            src="/butterdots.jpg"
            alt="butter dots in a metal bowl with ice"
            width={600}
            height={800}
            priority
            className="rounded-xl shadow-2xl w-full h-auto"
          />
        </div>

        <div className="max-w-2xl my-8">
          <p className="text-xl leading-relaxed text-gray-600">
            Butter Dots are small discs of butter (european style works best)
            which are formed in ice cold water by rolling bits of butter into a
            ball and then pressing them flat.
          </p>
        </div>

        <Button href="/resources" variant="primary" size="large">
          📚 Tibetan Fonts & Keyboard Resources
        </Button>
      </div>
    </Layout>
  )
}

export default Home
