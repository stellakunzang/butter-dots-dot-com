import type {NextPage} from 'next'
import {Layout} from '../components'
import {DictionaryEntry} from '../components/homepage'

const Home: NextPage = () => {
  return (
    <Layout
      title="Butter Dots"
      description="Butter Dots are small discs of butter formed in ice cold water"
    >
      <DictionaryEntry />
    </Layout>
  )
}

export default Home
