interface SpinnerProps {
  size?: number;
  className?: string;
}

export default function Spinner({ size = 48, className = "" }: SpinnerProps) {
  // Exact path lengths measured via getTotalLength()
  const houseDash = 84.06;
  const doorDash = 24;

  return (
    <div className={className} role="status" aria-label="Loading">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 32 32"
        fill="none"
        width={size}
        height={size}
      >
        <style>{`
          @keyframes draw-house {
            0% {
              stroke-dashoffset: ${houseDash};
            }
            50% {
              stroke-dashoffset: 0;
            }
            100% {
              stroke-dashoffset: -${houseDash};
            }
          }
          @keyframes draw-door {
            0%, 25% {
              stroke-dashoffset: ${doorDash};
            }
            50% {
              stroke-dashoffset: 0;
            }
            75%, 100% {
              stroke-dashoffset: -${doorDash};
            }
          }
        `}</style>
        {/* Animated house outline */}
        <path
          d="M16 4L3 15h4v12h18V15h4L16 4z"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
          strokeDasharray={houseDash}
          strokeDashoffset={houseDash}
          style={{ animation: "draw-house 1.6s ease-in-out infinite" }}
        />
        {/* Animated door */}
        <path
          d="M12 27V19h8v8"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
          strokeDasharray={doorDash}
          strokeDashoffset={doorDash}
          style={{ animation: "draw-door 1.6s ease-in-out infinite" }}
        />
      </svg>
    </div>
  );
}
