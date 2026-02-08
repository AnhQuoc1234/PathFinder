import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

interface MermaidProps {
  chartCode: string;
}

const MermaidChart: React.FC<MermaidProps> = ({ chartCode }) => {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 1. Khởi tạo cấu hình Mermaid
    mermaid.initialize({
      startOnLoad: false,
      theme: 'default',
      securityLevel: 'loose',
    });

    const renderChart = async () => {
      if (!chartCode || chartCode.length < 5) return;

      try {
        const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;

        // Render code into SVG
        const { svg } = await mermaid.render(id, chartCode);

        // add SVG into div
        if (ref.current) {
          ref.current.innerHTML = svg;
        }
      } catch (error) {
        console.error("Mermaid Error:", error);
        if (ref.current) {
          ref.current.innerHTML = `<div style="color:red; font-size:12px">Lỗi hiển thị sơ đồ. Code không hợp lệ.</div>`;
        }
      }
    };

    renderChart();
  }, [chartCode]);

  return (
    <div
      ref={ref}
      className="mermaid-container my-4 p-4 border rounded bg-white shadow-sm overflow-x-auto"
      style={{ minHeight: '100px' }} // Đảm bảo có chiều cao tối thiểu
    />
  );
};

export default MermaidChart;