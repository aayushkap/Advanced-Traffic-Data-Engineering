import { useState, useEffect } from "react";
import "./dashboard.css";
import TrafficVolume from "../traffic-volume";
import LaneUtilization from "../lane-utilization";
import AverageSpeed from "../average-speed";
import Filters from "../filters";

function Dashboard({ road, region }) {
  const [trafficData, setTrafficData] = useState(null);

  // Lift filter states to Dashboard so we can trigger re-fetch on change.
  const [timeFilter, setTimeFilter] = useState("Per Minute");
  const [liveUpdate, setLiveUpdate] = useState(false);
  const [history, setHistory] = useState(5);

  useEffect(() => {
    let intervalId;

    const fetchTrafficData = () => {
      console.log("Fetching traffic data...");
      fetch("http://localhost:8050/query_traffic_data", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          road,
          time_granularity: timeFilter,
          history: history,
        }),
      })
        .then((response) => response.json())
        .then((data) => setTrafficData(data))
        .catch((error) => console.error("Error fetching traffic data:", error));
    };

    // Initial API call on dependency change
    fetchTrafficData();

    // If live update is enabled, schedule the API call every 5 seconds.
    if (liveUpdate) {
      intervalId = setInterval(fetchTrafficData, 3000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [road, region, timeFilter, history, liveUpdate]);

  return (
    <>
      <div className="cols">
        <div className="title-card">
          <h1>{road}</h1>
        </div>
        <Filters
          timeFilter={timeFilter}
          setTimeFilter={setTimeFilter}
          liveUpdate={liveUpdate}
          setLiveUpdate={setLiveUpdate}
          history={history}
          setHistory={setHistory}
        />
      </div>
      <p>{region}</p>
      <div className="divider">
        <TrafficVolume trafficData={trafficData} />
      </div>
      <div className="cols">
        <div className="divider left">
          <AverageSpeed trafficData={trafficData} />
        </div>
        <div className="divider right">
          <LaneUtilization trafficData={trafficData} />
        </div>
      </div>
    </>
  );
}

export default Dashboard;
