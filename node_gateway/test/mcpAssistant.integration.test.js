/**
 * Tests d'intégration pour le routeur "MCP" du projet EnergIA
 * (le point d'entrée GET /assistant/assistant du node_gateway, qui normalise une
 * question en langage naturel via l'assistant/Ollama puis exécute l'action
 * correspondante contre python_service).
 *
 * Prérequis : la stack Docker doit être lancée (`docker compose up -d` à la
 * racine du projet) avant de lancer ces tests — ce sont des tests "boîte noire"
 * qui appellent la vraie API sur http://localhost:3000.
 *
 * Lancement :
 *   npm run test:integration
 *   (ou directement : node --test test/mcpAssistant.integration.test.js)
 *
 * L'URL de base peut être surchargée avec la variable d'env MCP_BASE_URL,
 * par exemple pour cibler un autre environnement :
 *   MCP_BASE_URL=http://localhost:4000 npm run test:integration
 *
 * Note : ces requêtes passent par un LLM (Ollama) et un calcul de simulation,
 * donc chaque appel peut prendre plusieurs secondes — les timeouts sont
 * volontairement généreux.
 */

const { test, describe, before } = require("node:test");
const assert = require("node:assert/strict");

const BASE_URL = process.env.MCP_BASE_URL || "http://localhost:3000";
const ASSISTANT_PATH = "/assistant/assistant";
const DEFAULT_TIMEOUT = 30_000;


async function askAssistant(question) {
  const url = new URL(ASSISTANT_PATH, BASE_URL);
  if (question !== undefined) {
    url.searchParams.set("request", question);
  }

  const res = await fetch(url);
  let body;
  try {
    body = await res.json();
  } catch {
    body = await res.text();
  }
  return { status: res.status, body };
}

describe("MCP assistant endpoint — disponibilité du service", () => {
  test(
    "le node_gateway répond sur / (sanity check avant de lancer la suite)",
    { timeout: 10_000 },
    async () => {
      let reachable = true;
      try {
        await fetch(BASE_URL);
      } catch (err) {
        reachable = false;
      }
      assert.ok(
        reachable,
        `Impossible de joindre ${BASE_URL}. La stack Docker est-elle lancée ? (docker compose up -d)`
      );
    }
  );
});

describe("MCP assistant endpoint — action GET_PLANTS", () => {
  test(
    "une question sur la liste des centrales renvoie la liste complète",
    { timeout: DEFAULT_TIMEOUT },
    async () => {
      const { status, body } = await askAssistant("Quelles sont les centrales françaises ?");

      assert.equal(status, 200);
      assert.ok(body.response, "la réponse doit contenir un champ 'response'");
      assert.ok(Array.isArray(body.response.plants), "response.plants doit être un tableau");
      assert.equal(
        body.response.count,
        body.response.plants.length,
        "count doit correspondre au nombre d'éléments de plants"
      );
      assert.ok(body.response.plants.length > 0, "la liste des centrales ne doit pas être vide");
      assert.ok(
        body.response.plants.includes("Gravelines"),
        "la centrale de Gravelines devrait figurer dans la liste"
      );
    }
  );
});

describe("MCP assistant endpoint — action GET_PROD_NATIONALE_HEURE", () => {
  test(
    "une question sur la production nationale à une heure donnée renvoie une répartition formatée",
    { timeout: DEFAULT_TIMEOUT },
    async () => {
      const { status, body } = await askAssistant("Donne moi la repartition de la production à 11h00");

      assert.equal(status, 200);
      assert.equal(typeof body.response, "string", "response doit être une chaîne de texte");
      assert.match(body.response, /^Répartition nationale à 11:00/);
      assert.match(
        body.response,
        /- .+ : \d+ MW/,
        "la réponse doit lister au moins une centrale avec sa puissance en MW"
      );
    }
  );
});

describe("MCP assistant endpoint — action GET_CONSO_REGION_HEURE", () => {
  test(
    "une question sur la consommation d'une région à une heure donnée renvoie une phrase formatée",
    { timeout: DEFAULT_TIMEOUT },
    async () => {
      const { status, body } = await askAssistant("Donne moi la consommation de la bretagne à 11h00");

      assert.equal(status, 200);
      assert.equal(typeof body.response, "string");
      assert.match(
        body.response,
        /^À 11:00, la consommation de la région bretagne est de \d+(\.\d+)? MW\.$/
      );
    }
  );

  test(
    "la normalisation régionale gère les anciens noms de région (ex: 'Centre')",
    { timeout: DEFAULT_TIMEOUT },
    async () => {
      const { status, body } = await askAssistant("Consommation de la région centre à 10h00");

      assert.equal(status, 200);
      assert.equal(typeof body.response, "string");

      assert.match(body.response, /centre_val_de_loire/);
    }
  );
});

describe("MCP assistant endpoint — action GET_PERTURBATION", () => {
  test(
    "une perturbation régionale renvoie une simulation par quart d'heure",
    { timeout: DEFAULT_TIMEOUT },
    async () => {
      const { status, body } = await askAssistant(
        "Il y a une augmentation pour l'occitanie de 200 Mw entre 12:00 et 14:30, donne moi la répartition de la production nucléaire sur la journée"
      );

      assert.equal(status, 200);
      assert.ok(Array.isArray(body.response), "response doit être un tableau (une entrée par quart d'heure)");
      assert.ok(body.response.length > 0, "la simulation doit couvrir au moins un pas de temps");

      const firstStep = body.response[0];
      assert.ok(Array.isArray(firstStep), "chaque pas de temps doit être un tableau de régions");
      assert.ok(firstStep.length > 0);

      const sample = firstStep[0];
      for (const key of [
        "region_id",
        "heure",
        "consommation_mw",
        "production_nucleaire_mw",
        "sens_variation",
      ]) {
        assert.ok(
          Object.prototype.hasOwnProperty.call(sample, key),
          `chaque enregistrement doit contenir la clé '${key}'`
        );
      }

      const hasOccitanie = body.response.some((step) =>
        step.some((region) => region.region_id === "occitanie")
      );
      assert.ok(hasOccitanie, "la région occitanie doit apparaître dans la simulation");
    }
  );
});

describe("MCP assistant endpoint — action UNKNOWN", () => {
  test(
    "une question hors périmètre renvoie le message de repli standard",
    { timeout: DEFAULT_TIMEOUT },
    async () => {
      const { status, body } = await askAssistant("Quelle est la recette de la quiche lorraine ?");

      assert.equal(status, 200);
      assert.equal(
        body.response,
        "Je n'ai pas les informations à ma disposition pour vous répondre"
      );
    }
  );
});

describe("MCP assistant endpoint — gestion des erreurs", () => {
  test(
    "un appel sans paramètre 'request' renvoie une erreur explicite",
    { timeout: 10_000 },
    async () => {
      const { status, body } = await askAssistant(undefined);

      assert.equal(status, 200);
      assert.equal(body.error, "Missing Question!");
    }
  );

  test(
    "un paramètre 'request' vide est traité comme une question absente",
    { timeout: 10_000 },
    async () => {
      const { status, body } = await askAssistant("");

      assert.equal(status, 200);
      assert.ok(body.error, "une chaîne vide devrait produire une erreur explicite");
    }
  );
});
