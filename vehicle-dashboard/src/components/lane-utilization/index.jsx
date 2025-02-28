import React from "react";
import { useState, useEffect } from "react";
import ReactECharts from "echarts-for-react";

const LaneUtilization = ({ trafficData }) => {
  // Sample data for lane utilization with trucks and cars
  // const data = [
  //   { lane: "Lane #1", cars: 80, trucks: 40 },
  //   { lane: "Lane #2", cars: 32, trucks: 38 },
  //   { lane: "Lane #3", cars: 90, trucks: 45 },
  //   { lane: "Lane #4", cars: 44, trucks: 32 },
  //   { lane: "Lane #5", cars: 75, trucks: 66 },
  // ];
  const [data, setData] = useState(null);
  useEffect(() => {
    if (trafficData && trafficData.result?.lane_utilization) {
      console.log("Setting data for average speed...", trafficData.result);
      setData(trafficData.result.lane_utilization);
    }
  }, [trafficData]);

  if (!data) return <></>;

  // Define one constant color for each series
  const carsColor = "#16dADEBB";
  const trucksColor = "#FF5CCCBB";

  // Create x-axis categories
  const lanes = data.map((item) => item.lane);

  // Calculate percentage data for each lane while keeping the absolute values
  const carsPercentData = data.map((item) => {
    const total = item.cars + item.trucks;
    const percentage = Math.round((item.cars / total) * 100);
    return { value: percentage, abs: item.cars };
  });

  const trucksPercentData = data.map((item) => {
    const total = item.cars + item.trucks;
    const percentage = Math.round((item.trucks / total) * 100);
    return { value: percentage, abs: item.trucks };
  });

  // Configure the ECharts option object
  const option = {
    backgroundColor: "#282828",
    tooltip: {
      trigger: "axis",
      formatter: (params) => {
        // Build the tooltip text for each lane using the absolute value (in brackets)
        let tooltipText = `${params[0].axisValue}<br/>`;
        params.forEach((item) => {
          tooltipText += `${item.marker} ${item.seriesName}: ${item.data.abs} (${item.value}%)<br/>`;
        });
        return tooltipText;
      },
    },
    legend: {
      data: ["Cars", "Trucks"],
      textStyle: { color: "#fff" },
      top: 10,
    },
    grid: {
      left: "5%",
      right: "5%",
      bottom: "0%",
      top: "15%",
      containLabel: true,
    },
    xAxis: {
      type: "category",
      data: lanes,
      axisLine: { lineStyle: { color: "#ccc" } },
      axisLabel: { color: "#ccc" },
    },
    yAxis: {
      type: "value",
      max: 100, // Ensure the y-axis goes from 0 to 100 (percent)
      axisLine: { lineStyle: { color: "#ccc" } },
      axisLabel: { color: "#ccc" },
      splitLine: { lineStyle: { color: "#444" } },
    },
    series: [
      {
        name: "Cars",
        type: "bar",
        stack: "total",
        data: carsPercentData,
        label: {
          show: true,
          position: "inside",
          color: "#fff",
          // Display the percentage on the bar
          formatter: (params) => `${params.value}%`,
        },
        itemStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0.1,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "#176BA0DD" },
              { offset: 1, color: "#16dADEDD" },
            ],
            global: false,
          },
        },
        barWidth: "35%",
      },
      {
        name: "Trucks",
        type: "bar",
        stack: "total",
        data: trucksPercentData,
        label: {
          show: true,
          position: "inside",
          color: "#fff",
          // Display the percentage on the bar
          formatter: (params) => `${params.value}%`,
        },
        itemStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0.0,
            x2: 0,
            y2: 0.5,
            colorStops: [
              { offset: 0.1, color: "#FF5CCCCC" },
              { offset: 1, color: "#DC52BFBB" },
            ],
            global: false,
          },
        },
        barWidth: "35%",
      },
    ],
  };

  return (
    <div style={{ height: "350px" }}>
      <h2>Lane Utilization</h2>
      <ReactECharts option={option} />
    </div>
  );
};

export default LaneUtilization;
