import { useState } from "react";
import { useEffect } from "react";
import { FiSettings, FiChevronRight } from "react-icons/fi";
import { FaRoad } from "react-icons/fa6";
import { PiMapPinArea } from "react-icons/pi";
import Dashboard from "./components/dashboard";
import "./App.css";

// const menus = {
//   Riyadh: {
//     submenus: ["Umm_Al_Qura_Road"],
//   },
//   Jeddah: {
//     submenus: ["King Abdulaziz Road"],
//   },
//   Dammam: {
//     submenus: ["Prince Mohammed bin Fahd Road"],
//   },
// };

function App() {
  const [menus, setMenus] = useState({});
  const [activeMenu, setActiveMenu] = useState(null);
  const [activeSubmenu, setActiveSubmenu] = useState(null);

  useEffect(() => {
    const fetchMetadata = () => {
      console.log("Fetching meta data...");
      fetch("http://localhost:8050/metadata", {
        method: "GET",
      })
        .then((response) => response.json())
        .then((data) => setMenus(data))
        .catch((error) => console.error("Error fetching traffic data:", error));
    };

    // Initial API call on dependency change
    fetchMetadata();
  }, []);

  const toggleMenu = (menuName) => {
    if (activeMenu === menuName) {
      setActiveMenu(null);
      setActiveSubmenu(null);
    } else {
      setActiveMenu(menuName);
      const firstSubmenu = menus[menuName]?.submenus[0] || null;
      setActiveSubmenu(firstSubmenu);
    }
  };

  const handleSubmenuClick = (submenuName) => {
    setActiveSubmenu(submenuName);
  };

  return (
    <div className="app-container">
      <div className="sidebar">
        <div className="logo">Traffic Dashboard</div>
        {Object.entries(menus).map(([name, { icon, submenus }]) => (
          <div className="menu-item" key={name}>
            <button
              className={`menu-button ${activeMenu === name ? "active" : ""}`}
              onClick={() => toggleMenu(name)}
            >
              <span className="menu-icon">
                <PiMapPinArea />
              </span>
              {name}
              {submenus.length > 0 && (
                <FiChevronRight
                  className={`chevron ${activeMenu === name ? "open" : ""}`}
                />
              )}
            </button>
            {submenus.length > 0 && (
              <div className={`submenu ${activeMenu === name ? "open" : ""}`}>
                {submenus.map((sub) => (
                  <a
                    href="#"
                    className={`submenu-item ${
                      activeSubmenu === sub ? "active" : ""
                    }`}
                    key={sub}
                    onClick={(e) => {
                      e.preventDefault();
                      handleSubmenuClick(sub);
                    }}
                  >
                    <FaRoad className="submenu-icon" />
                    <span className="submenu-text">{sub}</span>
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
      {!activeSubmenu && (
        <div className="main-content">
          <h1>Welcome to the Real-time Traffic Dashboard</h1>
          <p>Please select a region or road to begin.</p>
        </div>
      )}
      {activeSubmenu && (
        <div className="main-content">
          <Dashboard road={activeSubmenu} region={activeMenu} />
        </div>
      )}
    </div>
  );
}

export default App;
