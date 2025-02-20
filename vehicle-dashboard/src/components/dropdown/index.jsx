import { useState, useEffect, useRef } from "react";
import './Dropdown.css'

function CustomDropdown({ options, selected, onChange, bgColor }) {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Toggle the dropdown list visibility
  const toggleDropdown = () => {
    setOpen((prev) => !prev);
  };

  // When an option is clicked, update selection and close the dropdown
  const handleOptionClick = (value) => {
    onChange(value);
    setOpen(false);
  };

  // Close the dropdown if the user clicks outside of it
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () =>
      document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className={`custom-dropdown`} ref={dropdownRef}>
      <div className={`dropdown-header ${bgColor === "White" ? 'whiteBg':'blackBg'}`} onClick={toggleDropdown}>
        {selected}
        <span className={`arrow ${open ? 'open' : ''}`}></span>
      </div>
      {open && (
        <ul className="dropdown-list">
          {options.map((opt) => (
            <li
              key={opt.value}
              className="dropdown-list-item"
              onClick={() => handleOptionClick(opt.value)}
            >
              {opt.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default CustomDropdown;

