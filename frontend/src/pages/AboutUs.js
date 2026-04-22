// src/pages/AboutUs.js
import React from 'react';
import '../styles/Aboutus.css';

const AboutUs = () => {
  return (
    <div className="about-container">

      {/* Tech Stack */}
      <div className="tech-section">
        <h2>Technologies We Use</h2>
        <div className="tech-grid">
          
          <div className="tech-category">
            <h4>Frontend</h4>
            <div className="tech-tags">
              <span>React</span>
              <span>JavaScript</span>
              <span>CSS3</span>
              <span>Leaflet</span>
            </div>
          </div>

          <div className="tech-category">
            <h4>Backend</h4>
            <div className="tech-tags">
              <span>Python</span>
              <span>Flask</span>
              <span>Node.js</span>
              <span>Express</span>
            </div>
          </div>

          <div className="tech-category">
            <h4>Data & Analytics</h4>
            <div className="tech-tags">
              <span>Google Earth Engine</span>
              <span>Satellite Data</span>
              <span>Machine Learning</span>
              <span>GIS</span>
            </div>
          </div>

          <div className="tech-category">
            <h4>Deployment</h4>
            <div className="tech-tags">
              <span>Vercel</span>
              <span>Render</span>
              <span>CI/CD</span>
              <span>Docker</span>
            </div>
          </div>

        </div>
      </div>

    </div>
  );
};

export default AboutUs;