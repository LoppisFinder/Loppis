"use client";

import dynamic from "next/dynamic";
import { useI18n } from "@/lib/i18n/context";

const HomePage = dynamic(() => import("@/components/HomePage"), {
  ssr: false,
  loading: () => <LoadingScreen />,
});

function LoadingScreen() {
  const { t } = useI18n();
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        height: "100vh",
        color: "var(--color-text-muted)",
      }}
    >
      {t("loading")}
    </div>
  );
}

export default function Page() {
  return <HomePage />;
}
