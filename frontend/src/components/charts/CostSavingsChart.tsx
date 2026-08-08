import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  type ChartData,
  type ChartOptions,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

interface Props {
  data: {
    labels: string[]
    values: number[]
  }
  height?: number
}

export default function CostSavingsChart({ data, height = 280 }: Props) {
  const chartData: ChartData<'bar'> = {
    labels: data.labels,
    datasets: [
      {
        label: 'Cost (USD/month)',
        data: data.values,
        backgroundColor: [
          'rgba(99, 102, 241, 0.6)',
          'rgba(16, 185, 129, 0.6)',
          'rgba(6, 182, 212, 0.4)',
        ],
        borderColor: [
          'rgba(99, 102, 241, 1)',
          'rgba(16, 185, 129, 1)',
          'rgba(6, 182, 212, 1)',
        ],
        borderWidth: 2,
        borderRadius: 8,
        borderSkipped: false,
      },
    ],
  }

  const options: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        borderColor: 'rgba(99, 102, 241, 0.3)',
        borderWidth: 1,
        titleColor: '#f1f5f9',
        bodyColor: '#94a3b8',
        padding: 12,
        callbacks: {
          label: (ctx) => {
            const val = ctx.parsed.y;
            return val !== null ? `$${val.toFixed(2)}/mo` : '';
          },
        },
      },
    },
    scales: {
      x: {
        grid: { color: 'rgba(99, 102, 241, 0.06)' },
        ticks: { color: '#94a3b8', font: { size: 12 } },
        border: { color: 'transparent' },
      },
      y: {
        grid: { color: 'rgba(99, 102, 241, 0.06)' },
        ticks: {
          color: '#94a3b8',
          font: { size: 11 },
          callback: (v) => `$${v}`,
        },
        border: { color: 'transparent' },
      },
    },
  }

  return (
    <div className="chart-container" style={{ height }}>
      <Bar data={chartData} options={options} />
    </div>
  )
}
