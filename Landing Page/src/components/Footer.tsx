import React from "react";

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <span className="logo" style={{ fontSize: '1rem' }}>
          <span className="logo-mark" style={{ width: 22, height: 22 }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
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
