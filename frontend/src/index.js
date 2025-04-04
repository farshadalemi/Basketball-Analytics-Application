import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';

// Import axios configuration
import './config/axios';

const container = document.getElementById('root');
const root = createRoot(container);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
