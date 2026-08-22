import next from "eslint-config-next";

/**
 * Flat config, native.
 *
 * Previously this wrapped `eslint-config-next` in `FlatCompat`, the shim for
 * consuming legacy eslintrc-style configs. From v16 the package ships a real
 * flat config, and running it back through the shim crashes ESLint with a
 * circular-structure error while it tries to serialise the plugin graph.
 */
const eslintConfig = [
  ...next,
  {
    rules: {
      "react/no-unescaped-entities": "off",
      "@next/next/no-page-custom-font": "off",

      // Two React Compiler rules that arrived with Next 16 and flag 13
      // existing call sites. They are warnings here, not errors, and that is
      // a deliberate deferral rather than a dismissal.
      //
      // They are heuristics about a real cost: setState in an effect body can
      // cascade renders. But they also flag correct code. ElapsedTimer sets
      // state from a setInterval callback, which is exactly the "subscribe to
      // an external system" case the rule's own message endorses, and
      // useApi's loading flag is a genuine external-fetch lifecycle.
      //
      // Some of the 13 are worth fixing: deriving a default selection inside
      // an effect (explore page) should be computed during render instead.
      // That is a refactor with its own risk, and doing it inside a framework
      // upgrade would confound two changes. Left visible so it gets done.
      "react-hooks/set-state-in-effect": "warn",
      "react-hooks/use-memo": "warn",
    },
  },
  {
    ignores: [".next/**", ".next-build/**", "node_modules/**", "next-env.d.ts"],
  },
];

export default eslintConfig;
