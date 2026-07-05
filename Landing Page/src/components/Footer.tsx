import React from "react";

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <span className="logo" style={{ fontSize: '1rem' }}>
          <span className="logo-mark" style={{ width: 22, height: 22, background: 'transparent' }}>
            <img src="/logo.png" alt="Rakshastra Logo" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
          </span>
          Rakshastra
        </span>

        <div className="footer-links">
          <a href="#" className="footer-link">GitHub</a>
          <a href="#" className="footer-link">Docs</a>
          <a href="#" className="footer-link">Discord</a>
          <a href="#" className="footer-link">Twitter</a>
        </div>

        <span className="footer-copy">
          &copy; {new Date().getFullYear()} Rakshastra Project
        </span>
      </div>
    </footer>
  );
}
