# AI Deployment Orchestrator - UI# React + Vite



A lean, focused React UI for the AI Deployment Orchestrator, built with Material-UI and showcasing autonomous agentic behavior.This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.



## 🚀 FeaturesCurrently, two official plugins are available:



### Core Pages- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh

- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

1. **Dashboard** - Landing page with:

   - Key metrics (Total Devices, Active Deployments, AI Cohorts)## React Compiler

   - Recent AI Activity feed showing autonomous decisions

   - Device Distribution by Ring (Donut Chart)The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).



2. **Devices** - Device management with:## Expanding the ESLint configuration

   - Comprehensive device table with hardware specs

   - AI-assigned ring categorizationIf you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

   - Risk scores calculated by AI
   - Device detail drawer with performance metrics
   - AI reasoning for ring assignments
   - Manual override capability

3. **Deployments** - Deployment orchestration with:
   - Deployment list with status badges
   - Progress indicators
   - Create deployment wizard (3-step process)
   - AI chat customization option

4. **Deployment Detail** - Real-time deployment monitoring with:
   - Ring-by-ring progress flow
   - Accordion view for each ring
   - AI reasoning display when gating occurs
   - Device-level status tables
   - Automatic pause/stop decisions by AI

5. **Rings Configuration** - Ring policy management with:
   - Configuration cards for each ring (Ring 0-4)
   - Monitoring settings (duration, wait times)
   - Gating thresholds (success rate, anomaly rate)
   - AI decision rules (pause/stop/continue)
   - Edit modal for detailed configuration

6. **Settings** - System configuration with:
   - SuperOps simulation settings
   - AI model configuration
   - Default anomaly thresholds

## 🛠️ Tech Stack

- **React 19** - UI framework
- **Vite** - Build tool and dev server
- **Material-UI (MUI)** - Material Design components
- **React Router** - Client-side routing
- **Recharts** - Chart library for data visualization
- **Emotion** - CSS-in-JS styling

## 📦 Installation

```bash
cd ui
npm install
```

## 🏃 Running the App

```bash
npm run dev
```

The app will be available at `http://localhost:5173/`

## 📁 Project Structure

```
ui/
├── src/
│   ├── components/       # Reusable components
│   │   └── Layout.jsx    # Main layout with sidebar navigation
│   ├── pages/            # Page components
│   │   ├── Dashboard.jsx
│   │   ├── Devices.jsx
│   │   ├── Deployments.jsx
│   │   ├── DeploymentDetail.jsx
│   │   ├── Rings.jsx
│   │   └── Settings.jsx
│   ├── data/             # Mock data
│   │   └── mockData.js   # All mock data for the application
│   ├── theme/            # Material-UI theme
│   │   └── theme.js      # Custom theme configuration
│   ├── App.jsx           # Main app component with routing
│   ├── main.jsx          # Entry point
│   └── index.css         # Global styles
├── package.json
└── vite.config.js
```

## 🎨 Design Philosophy

This UI is designed to showcase **autonomous agentic AI behavior**:

- **No passive dashboards** - Every feature demonstrates AI making decisions
- **AI reasoning is prominent** - Users see why AI made each decision
- **Clean, focused UX** - No feature bloat, only core capabilities
- **Material Design** - Google's design system for consistency
- **Responsive layout** - Works on desktop and mobile

## 🎯 Key Design Patterns

### Ring Color Coding
- **Ring 0 (Canary)**: Purple `#9c27b0`
- **Ring 1 (Low Risk)**: Green `#4caf50`
- **Ring 2 (Medium Risk)**: Blue `#2196f3`
- **Ring 3 (High Risk)**: Orange `#ff9800`
- **Ring 4 (VIP)**: Red `#f44336`

### Status Indicators
- **🟡 Paused**: Warning (Yellow)
- **⏳ In Progress**: Info (Blue)
- **✅ Complete**: Success (Green)
- **❌ Failed**: Error (Red)

## 🔄 Next Steps

This is a **mock UI** with static data. To integrate with the backend:

1. Replace mock data imports with API calls
2. Add state management (React Context or Redux)
3. Implement real-time updates (WebSockets or polling)
4. Add authentication/authorization
5. Connect to actual SuperOps API
6. Integrate with AI models (Amazon Nova Act / Qwen3)

## 📝 Mock Data

Currently using static mock data in `src/data/mockData.js`:
- 5 sample devices across all rings
- 3 deployments (1 paused, 2 complete)
- Detailed deployment data for Ring 0-4
- Ring configuration data
- AI activity feed
- Dashboard metrics

## 🧪 Build for Production

```bash
npm run build
```

Built files will be in the `dist/` directory.

## 📄 License

Part of the FlexDeploy AI Deployment Orchestrator project.
