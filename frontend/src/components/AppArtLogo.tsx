interface AppArtLogoProps {
  className?: string;
  size?: number;
}

export default function AppArtLogo({ className = "", size = 24 }: AppArtLogoProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 32 32"
      fill="none"
      width={size}
      height={size}
      className={className}
    >
      {/* House outline */}
      <path
        d="M16 4L3 15h4v12h18V15h4L16 4z"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      {/* Door */}
      <path
        d="M12 27V19h8v8"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  );
}
