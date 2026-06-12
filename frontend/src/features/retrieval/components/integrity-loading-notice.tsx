import { Notice } from "../../../components/ui/notice";

export function IntegrityLoadingNotice() {
  return (
    <Notice title="Integrity check running">
      The app is checking trusted source hashes against the active index.
    </Notice>
  );
}
