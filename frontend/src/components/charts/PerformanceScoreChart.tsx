import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  type ChartData,
  type ChartOptions,
} from 'chart.js'
import { Radar } from 'react-chartjs-2'

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip)

interface Props {
  scores: {
    label: string
    current: number
    predicted: number
  }[]
  height?: number
}

export default function PerformanceScoreChart({ scores, height = 280 }: Props) {
  const chartData: ChartData<'radar'> = {
    labels: scores.map((s) => s.label),
    datasets: [
      {
        label: 'Current',
        data: scores.map((s) => s.current),
        borderColor: 'rgba(99, 102, 241, 1)',
        backgroundColor: 'rgba(99, 102, 241, 0.12)',
        pointBackgroundColor: 'rgba(99, 102, 241, 1)',
        pointRadius: 4,
        borderWidth: 2,
      },
      {
        label: 'Predicted (Rightsized)',
        data: scores.map((s) => s.predicted),
        borderColor: 'rgba(16, 185, 129, 1)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        pointBackgroundColor: 'rgba(16, 185, 129, 1)',
        pointRadius: 4,
        borderWidth: 2,
      },
    ],
  }

  const options: ChartOptions<'radar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        labels: {
          color: '#94a3b8',
          usePointStyle: true,
          pointStyleWidth: 10,
          font: { size: 11 },
          boxHeight: 4,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        borderColor: 'rgba(99, 102, 241, 0.3)',
        borderWidth: 1,
        titleColor: '#f1f5f9',
        bodyColor: '#94a3b8',
        padding: 10,
      },
    },
    scales: {
      r: {
        min: 0,
        max: 100,
        ticks: {
          color: '#475569',
          backdropColor: 'transparent',
          font: { size: 9 },
          stepSize: 20,
        },
        grid: { color: 'rgba(99, 102, 241, 0.1)' },
        pointLabels: { color: '#94a3b8', font: { size: 11 } },
        angleLines: { color: 'rgba(99, 102, 241, 0.08)' },
      },
    },
  }

  return (
    <div className="chart-container" style={{ height }}>
      <Radar data={chartData} options={options} />
    </div>
  )
}
