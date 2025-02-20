import { useState } from 'react';
import './dashboard.css';
import TrafficVolume from '../traffic-volume';
import LaneUtilization from '../lane-utilization';
import AverageSpeed from '../average-speed';
import Filters from '../filters';

function Dashboard({ road , region }) {
    return (
        <>
            <div className="cols">
                <div className="title-card">
                    <h1>{road}</h1>
                </div>
                <Filters />
            </div>
            <p>{region}</p>
            <div className="divider">
                <TrafficVolume />
            </div>
            <div className="cols">
                <div className="divider left">
                    <AverageSpeed />
                </div>
                <div className="divider right">
                    <LaneUtilization />
                </div>
            </div>
        </>
    )
}

export default Dashboard;