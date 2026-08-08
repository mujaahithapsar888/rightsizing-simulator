import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
  Filler,
  type ChartData,
  type ChartOptions,
} from 'chart.js'
import { Line } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, Tooltip, Filler)

interface Props {
  timestamps: string[]
  values: number[]
  height?: number
  threshold?: number
}

export default function MemoryUtilChart({ timestamps, values, height = 220, threshold = 85 }: Props) {
  const chartData: ChartData<'line'> = {
    labels: timestamps,
    datasets: [
      {
        label: 'Memory Utilization (%)',
        data: values,
        borderColor: 'rgba(6, 182, 212, 1)',
        backgroundColor: 'rgba(6, 182, 212, 0.08)',
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: 'rgba(6, 182, 212, 1)',
        fill: true,
        tension: 0.4,
      },
      {
        label: 'Threshold',
        data: timestamps.map(() => threshold),
        borderColor: 'rgba(245, 158, 11, 0.7)',
        borderDash: [6, 4],
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
        tension: 0,
      },
    ],
  }

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        labels: {
          color: '#94a3b8',
          usePointStyle: true,
          pointStyleWidth: 12,
          font: { size: 11 },
          boxHeight: 4,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        borderColor: 'rgba(6, 182, 212, 0.3)',
        borderWidth: 1,
        titleColor: '#f1f5f9',
        bodyColor: '#94a3b8',
        padding: 10,
        callbacks: {
          label: (ctx) => {
            const val = ctx.parsed.y;
            return ctx.datasetIndex === 0
              ? `Memory: ${val !== null ? val.toFixed(1) : ''}%`
              : `Threshold: ${threshold}%`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: { color: 'rgba(6, 182, 212, 0.06)' },
        ticks: { color: '#94a3b8', font: { size: 10 }, maxTicksLimit: 8 },
        border: { color: 'transparent' },
      },
      y: {
        min: 0,
        max: 100,
        grid: { color: 'rgba(6, 182, 212, 0.06)' },
        ticks: {
          color: '#94a3b8',
          font: { size: 11 },
          callback: (v) => `${v}%`,
        },
        border: { color: 'transparent' },
      },
    },
  }

  return (
    <div className="chart-container" style={{ height }}>
      <Line data={chartData} options={options} />
    </div>
  )
}
