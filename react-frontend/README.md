# Frederick Platform - Next.js + React Frontend

A modern React/Next.js frontend for the Frederick Semantic Mapping Platform.

## Tech Stack

- **Framework**: Next.js 14 + React
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Charts**: react-plotly.js (https://github.com/plotly/react-plotly.js)
- **Icons**: Lucide React
- **HTTP Client**: Axios

## Features (Frontend Only)

- **Semantic Term Mapping** - Map medical terms across different terminology systems
- **AI Assistant** - Chat interface with GPT-4 for semantic mapping queries
- **Graph Visualization** - Interactive Neo4j graph visualization with Plotly
- **Analytics Dashboard** - Real-time metrics and performance monitoring
- **Feedback Portal** - Expert feedback collection system
- **Results Analysis** - Comprehensive analysis and comparison tools


## Getting Started

### Prerequisites

- Node.js 18+ and pnpm

### Installation

1. Navigate to the frontend directory:
```bash
cd react-frontend
```

2. Install dependencies:


```bash
# 
npm install pnpm
npx pnpm install
```

### Development

Run the development server:

```bash
# 
npx pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Building for Production

```bash
pnpm run build
pnpm start
```

## Project Structure

```
react-frontend/
├── app/
│   ├── globals.css          # Global styles and Tailwind imports
│   ├── layout.tsx           # Root layout component
│   └── page.tsx             # Main page with routing
├── components/
│   ├── AppSidebar.tsx          # Navigation sidebar
│   └── pages/
│       ├── Dashboard.tsx           # Dashboard page
│       ├── SemanticMapping.tsx    # Semantic mapping page
│       ├── AIChat.tsx              # AI chat interface
│       └── GraphVisualization.tsx # Graph visualization
├── lib/
│   └── api.ts               # API client for backend communication
└── package.json
```

## Customization

### Changing Colors

Edit `tailwind.config.js` to customize the color scheme:

```js
colors: {
  primary: { ... },
  dark: { ... }
}
```

### Adding New Pages

1. Create a new file in `components/pages/`
2. Add a new item in `components/AppSidebar.tsx`
3. Add the route in `app/page.tsx`


## Troubleshooting

### Plotly Charts Not Rendering

- Ensure `react-plotly.js` is installed
- Check browser console for errors

## How to use Makefile
- from inside, react-frontend path, use command `make dev`
- this will install pnpm locally (if not already installed), project dependencies, and start next.js on port 4000.

© 2025 Frederick Platform

