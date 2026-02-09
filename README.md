# Butter Dots Dot Com

A delightful Next.js website showcasing the art of butter dots - small discs of butter formed in ice cold water.

## Prerequisites

- Node.js 14.x or later
- npm or yarn package manager

## Local Development

### First Time Setup

1. Clone the repository and navigate to the project directory:
```bash
git clone <your-repo-url>
cd butter-dots-dot-com
```

2. Install dependencies:
```bash
yarn install
# or
npm install
```

### Running the Development Server

Start the development server:

```bash
yarn dev
# or
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to see the result.

The page will automatically update as you edit files. The main page is located at `pages/index.tsx`.

### Building for Production

To test the production build locally:

```bash
# Build the application
yarn build
# or
npm run build

# Start the production server
yarn start
# or
npm start
```

## Project Structure

```
├── pages/              # Next.js pages and routing
│   ├── index.tsx       # Home page
│   └── api/            # API routes
├── public/             # Static assets (images, favicon)
│   └── butterdots.jpg  # Main butter dots image
├── styles/             # CSS modules and global styles
│   ├── Home.module.css # Homepage styles
│   └── globals.css     # Global styles
└── package.json        # Dependencies and scripts
```

## Deployment

### Deploying to Vercel (Recommended)

Vercel is the easiest way to deploy Next.js apps and is created by the Next.js team.

#### Option 1: Deploy via Git Integration (Recommended)

1. Push your code to GitHub, GitLab, or Bitbucket
2. Go to [vercel.com](https://vercel.com/new)
3. Import your repository
4. Vercel will automatically detect Next.js and configure build settings
5. Click "Deploy"

**Automatic deployments**: After initial setup, every push to your main branch automatically deploys to production, and every pull request gets a preview URL.

#### Option 2: Deploy via Vercel CLI

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Run deployment command from your project directory:
```bash
vercel
```

3. Follow the prompts to link your project

4. For production deployment:
```bash
vercel --prod
```

### Deploying Changes

Once set up with git integration:

1. Make your changes locally
2. Test locally with `yarn dev`
3. Commit your changes:
```bash
git add .
git commit -m "Description of your changes"
```
4. Push to your repository:
```bash
git push origin main
```
5. Vercel automatically builds and deploys your changes (usually takes 30-60 seconds)
6. You'll receive a deployment URL in your Vercel dashboard

### Other Deployment Options

- **Netlify**: Connect your git repository at [netlify.com](https://netlify.com)
- **AWS Amplify**: Use the Amplify Console to deploy from git
- **Self-hosted**: Build with `yarn build` and serve the `.next` folder with `yarn start`

## Image Optimization

The butter dots image is optimized for web:
- Resized to 900×1200px (maintains 3:4 aspect ratio)
- Compressed to ~331KB for fast loading
- Uses Next.js Image component for automatic optimization

To optimize new images:
```bash
# Install ImageMagick or use sips (macOS)
sips -Z 1200 --setProperty format jpeg --setProperty formatOptions 80 input.jpg --out output.jpg
```

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Learn Next.js](https://nextjs.org/learn)
- [Next.js GitHub Repository](https://github.com/vercel/next.js)

## Support

For issues or questions, please open an issue in the repository.
