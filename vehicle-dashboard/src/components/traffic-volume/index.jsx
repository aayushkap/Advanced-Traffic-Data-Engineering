import React from 'react';
import ReactECharts from 'echarts-for-react';
import { color } from 'echarts';

const TrafficVolume = () => {
  // Sample data: each object represents a day
  const data = [
    { date: '2025-01-01', cars: 120, trucks: 40, violations: 25 },
    { date: '2025-01-02', cars: 132, trucks: 35, violations: 15  },
    { date: '2025-01-03', cars: 101, trucks: 23, violations: 32  },
    { date: '2025-01-04', cars: 134, trucks: 20, violations: 61  },
    { date: '2025-01-05', cars: 90, trucks: 80 , violations: 40 },
    { date: '2025-01-06', cars: 100, trucks: 32, violations: 12  },
    { date: '2025-01-07', cars: 150, trucks: 76, violations: 55  },
    
  ];

  // Format Dates as Text
  data.forEach(item => {
    const date = new Date(item.date);
    item.date = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  });

  // Prepare the data arrays for the chart
  const dates = data.map(item => item.date);
  const carsData = data.map(item => item.cars);
  const trucksData = data.map(item => item.trucks);
  const totalData = data.map(item => item.cars + item.trucks);

  // Configure the ECharts option object
  const option = {
    backgroundColor: '#282828',
    tooltip: {
      trigger: 'axis',
    },
    legend: {
      data: ['Cars', 'Trucks', 'Total Vehicles', 'Total Violations'],
      textStyle: { color: '#FFFFFF' }, // Legend text color
      selected: {
        'Total Violations': false // Keep 'Total Violations' legend off by default
      }
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#999' } }, // Axis color
      axisLabel: { color: '#CCC' } // Label color
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#CCC' } },
      axisLabel: { color: '#CCC' },
      splitLine: { lineStyle: { color: '#444' } } // Make gridlines dim
    },
    grid: {
      left: '3%',
      right: '3%',
      bottom: '1%',
      containLabel: true
    },
    series: [
      {
        name: 'Cars',
        type: 'bar',
        data: carsData,
        label: {
          show: true,
          position: 'top',
          color: '#FFFFFF', // Set label text color to white
          formatter: '{c}'
        },
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0.1,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#176BA0BB' },
              { offset: 1, color: '#16dADEBB' }
            ],
            global: false
          }
        }
      },
      {
        name: 'Trucks',
        type: 'bar',
        data: trucksData,
        label: {
          show: true,
          position: 'top',
          color: '#FFFFFF',
          formatter: '{c}'
        },
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0.0,
            x2: 0,
            y2: 0.5,
            colorStops: [
              { offset: 0.1, color: '#FF5CCCBB' },
              { offset: 1, color: '#DC52BFAA' }
            ],
            global: false
          }
        }
      },
      {
        name: 'Total Vehicles',
        type: 'line',
        data: totalData,
        smooth: true,
        label: {
          show: true,
          position: 'top',
          formatter: function (params) {
            const currentValue = params.value;
            const prevValue = params.dataIndex > 0 ? totalData[params.dataIndex - 1] : null;
            let diff = null;
            let diffText = '';
            if (prevValue !== null) {
                diff = currentValue - prevValue;
                const diffPercentage = ((diff / prevValue) * 100).toFixed(0);
                const arrow = diff > 0 ? '↑' : diff < 0 ? '↓' : '';
                diffText = `${arrow} (${diffPercentage}%)`;
            }
            const diffStyle = diff > 0 ? '{diffPos|' + diffText + '}' : diff < 0 ? '{diffNeg|' + diffText + '}' : '{diff|' + diffText + '}';
            return '{value|' + currentValue + '}\n' + diffStyle;
        },
        rich: {
            value: { fontSize: 14, fontWeight: '600', color: '#ccc' },
            diffPos: { fontSize: 10, color: '#00CC00', verticalAlign: 'bottom', fontWeight: 'bold' },
            diffNeg: { fontSize: 10, color: 'red', verticalAlign: 'bottom', fontWeight: 'bold' },
            diff: { fontSize: 10, color: '#FFF', verticalAlign: 'bottom', fontWeight: 'bold' }
        },
        },
        lineStyle: {
          width: 1.5,
          color: '#DC52BF'
        },
        itemStyle: {
          color: '#16dADEBB'
        }
      },
      {
        name: 'Total Violations',
        type: 'line',
        data: data.map(item => item.violations),
        smooth: true,
        label: {
          show: true,
          position: 'top',
          color: '#FF5500FF',
          formatter: '{value|{c}}\n{label|}',
          rich: {
            value: { fontSize: 14, fontWeight: 'bold', color: '#FF5500', padding: [0, 0, -10, 0] },
            label: { fontSize: 12, fontWeight: 'bold', color: '#FF5500' },
          },
        },
        lineStyle: {
          width: 3,
          color: '#FF5500FF'
        },
        itemStyle: {
          color: '#FF5500FF'
        }
      }
    ]
  };

  return (
    <div>
      <h2>Traffic Volume</h2>
      <ReactECharts option={option} style={{ 'min-height': '500px', width: '100%' }} />
    </div>
  );
};

export default TrafficVolume;
