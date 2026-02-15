import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

const PUBLISHABLE_KEY = (typeof process !== 'undefined' && process.env?.CLERK_PUBLISHABLE_KEY) || '';
const root = ReactDOM.createRoot(rootElement);

if (PUBLISHABLE_KEY) {
  // With Clerk: Full auth mode
  import('@clerk/clerk-react').then(({ ClerkProvider }) => {
    root.render(
      <React.StrictMode>
        <ClerkProvider publishableKey={PUBLISHABLE_KEY} afterSignOutUrl="/">
          <App />
        </ClerkProvider>
      </React.StrictMode>
    );
  });
} else {
  // Without Clerk: Dev/demo mode - render app directly
  console.info('[Smarty AI] Running in dev mode (no Clerk key). Auth bypassed.');
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}