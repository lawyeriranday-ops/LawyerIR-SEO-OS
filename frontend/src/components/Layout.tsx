import { ReactNode } from "react";
import "./Layout.css";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="layout">
      <header className="layout__header">
        <h1>LawyerIR SEO OS</h1>
        <p>AI-powered SEO management for LawyerIR.com</p>
      </header>
      <main className="layout__main">{children}</main>
    </div>
  );
}
