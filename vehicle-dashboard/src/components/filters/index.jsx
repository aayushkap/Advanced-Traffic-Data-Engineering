import { useState } from "react";
import "./Filters.css";
import CustomDropdown from "../dropdown";

export default function Filters({
  timeFilter,
  setTimeFilter,
  liveUpdate,
  setLiveUpdate,
  history,
  setHistory,
}) {
  const historyOptions = [5, 10, 25, 50, 100, 250, 500, 1000];

  const handleHistoryChange = (value) => {
    const currentIndex = historyOptions.indexOf(value);
    return {
      increment:
        historyOptions[Math.min(currentIndex + 1, historyOptions.length - 1)],
      decrement: historyOptions[Math.max(currentIndex - 1, 0)],
    };
  };

  const handleInputChange = (e) => {
    const currentValue = parseInt(e.target.value, 10);
    if (historyOptions.includes(currentValue)) {
      setHistory(currentValue);
    }
  };

  return (
    <div className="filters-container">
      <label className="filter-container">
        <CustomDropdown
          options={[
            { label: "Per Minute", value: "Per Minute" },
            { label: "Per Hour", value: "Per Hour" },
            { label: "Per Day", value: "Per Day" },
          ]}
          selected={timeFilter}
          onChange={(timeValue) => setTimeFilter(timeValue)}
          bgColor={"White"}
        />
        Group By
      </label>

      <label className="filter-container">
        <button
          className="history-button"
          disabled={history === historyOptions[0]}
          onClick={() => setHistory(handleHistoryChange(history).decrement)}
        >
          -
        </button>
        <input
          className="history-input"
          type="number"
          value={history}
          readOnly
        />
        <button
          className="history-button"
          disabled={history === historyOptions[historyOptions.length - 1]}
          onClick={() => setHistory(handleHistoryChange(history).increment)}
        >
          +
        </button>
        History
      </label>

      <label className="filter-container switch">
        <input
          type="checkbox"
          checked={liveUpdate}
          onChange={() => setLiveUpdate(!liveUpdate)}
        />
        <span className="slider"></span>
        <span className="switch-label">Live Update</span>
      </label>
    </div>
  );
}
