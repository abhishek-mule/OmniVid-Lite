// helpers.ts
export function renderBackgroundStyle(bg: any, meta: any) {
  if (!bg) return {};
  if (bg.type === "solid") {
    return { backgroundColor: bg.value || "#000" };
  }
  if (bg.type === "gradient") {
    return { background: `linear-gradient(${bg.value?.join(", ") || "#000, #fff"})` };
  }
  return {};
}