import React, { useState } from "react";
import ReactECharts from "echarts-for-react";
import * as echarts from "echarts";
import "./average-speed.css";
import CustomDropdown from "../dropdown";

// Data for the vehicles
const data = {
  count: {
    cars: 200,
    trucks: 120,
  },
  speedingCount: {
    cars: 55,
    trucks: 15,
  },
  speedLimit: {
    cars: 100,
    trucks: 80,
  },
  avgSpeed: {
    cars: 100,
    trucks: 60,
  },
};

function AverageSpeed() {
  const [selectedVehicle, setSelectedVehicle] = useState("cars");

  // Retrieve the dynamic values based on the selected vehicle type.
  const totalVehicles = data.count[selectedVehicle];
  const speedingVehicles = data.speedingCount[selectedVehicle];
  const speedLimit = data.speedLimit[selectedVehicle];
  const avgSpeed = data.avgSpeed[selectedVehicle];

  // Gauge maximum is set to speed limit + 20.
  const gaugeMax = speedLimit + 20;
  // Calculate the ratio for the “safe” section.
  const safeRatio = speedLimit / gaugeMax;
  // Calculate percentage for the progress bar.
  const speedingPercentage =
    totalVehicles > 0
      ? Math.round((speedingVehicles / totalVehicles) * 100)
      : 0;

  // ECharts gauge option
  const option = {
    series: [
      {
        type: "gauge",
        radius: "100%",
        min: 0,
        max: Math.ceil((gaugeMax + 0) / 10) * 10,
        splitNumber: 5,
        axisLine: {
          lineStyle: {
            width: 25,
            color: [
              [safeRatio * 0.8, "#16dADEBB"],
              [safeRatio, "#DD8800"],
              [1, "#FF0000BB"],
            ],
          },
        },
        pointer: {
          itemStyle: {
            color: "#fff",
          },
        },
        axisTick: {
          distance: -10,
          length: 8,
          lineStyle: {
            color: "#DDD",
            width: 2,
          },
        },
        splitLine: {
          distance: -25,
          length: 25,
          lineStyle: {
            color: "#DDD",
            width: 2,
          },
        },
        axisLabel: {
          color: "#ccc",
          distance: 30,
          fontSize: 13,
        },
        detail: {
          valueAnimation: true,
          formatter: "{value} km/h",
          color: "#fff",
          fontSize: 16,
          rich: {
            title: {
              fontSize: 8,
              color: "#fff",
              padding: [0, 0, 0, 0],
            },
          },
        },
        data: [
          {
            value: avgSpeed,
            name: "Average Speed",
          },
        ],
      },
    ],
  };

  // Options for the dropdown
  const vehicleOptions = [
    { value: "cars", label: "Cars" },
    { value: "trucks", label: "Trucks" },
  ];

  return (
    <div className="average-speed-wrapper">
      <div className="header">
        <h2>Average Speed</h2>
        <CustomDropdown
          options={vehicleOptions}
          selected={selectedVehicle}
          onChange={(val) => setSelectedVehicle(val)}
        />
      </div>

      <div className="average-speed-container">
        {/* Left-hand side: speed stats */}
        <div className="speed-stats">
          <div className="speed-limit">
            <span className="value-title">Road Speed Limit</span> <br />
            <span className="value-main">{speedLimit}</span>
            <span className="value-sub"> km/h</span>
          </div>
          <div className="speeding-info">
            <span className="value-title">Speeding Vehicles</span> <br />
            <span className="value-main">{speedingVehicles}</span>{" "}
            <span className="value-sub">/ {totalVehicles}</span>
            <div className="progress-bar">
              <div
                className={`progress ${
                  speedingPercentage > 50 ? "high" : "medium"
                }`}
                style={{ width: `${speedingPercentage}%` }}
              >
                {speedingPercentage <= 0 ? null : speedingPercentage + "%"}
              </div>
            </div>
          </div>
        </div>

        <div className="gauge-container">
          <ReactECharts
            option={option}
            style={{ width: "100%", height: "100%" }}
          />
        </div>
      </div>
    </div>
  );
}

export default AverageSpeed;
