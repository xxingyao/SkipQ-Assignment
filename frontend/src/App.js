import React from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

import { AuthProvider } from './auth/AuthContext';
import { RequireRole } from './auth/RequireRole';
import { SignIn } from './Pages/SignIn';
import { DinerShell } from './Pages/diner/DinerShell';
import { VendorShell } from './Pages/vendor/VendorShell';

// One route per persona area, each nested so every screen inside it inherits
// the same guard and the same chrome. The lab's flat /STX, /OM, /EXP, /MNG
// could not do that: a new screen had to repeat the gate itself.
export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<SignIn />} />
          <Route path="/diner/*" element={
            <RequireRole role="Diner"><DinerShell /></RequireRole>
          } />
          <Route path="/vendor/*" element={
            <RequireRole role="Vendor"><VendorShell /></RequireRole>
          } />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}