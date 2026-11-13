import '../styles/globals.css'
import type { AppProps } from 'next/app'
import { initMonitoring } from '../lib/monitoring'

initMonitoring()

function MyApp({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />
}

export default MyApp
