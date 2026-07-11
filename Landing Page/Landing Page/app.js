#!/usr/bin/env node

/**
 * ============================================================================
 * RAKSHASTRA (रक्षास्त्र) — Autonomous Cyber Defense Agent (CLI Simulator)
 * ============================================================================
 * A runnable Node.js terminal application demonstrating the crawler,
 * Gemini NLP parser, and Neo4j identity resolver workflows.
 * 
 * Usage: node app.js
 * ============================================================================
 */

const readline = require("readline");

// Terminal Colors Helper
const Colors = {
  reset: "\x1b[0m",
  bright: "\x1b[1m",
  dim: "\x1b[2m",
  underscore: "\x1b[4m",
  blink: "\x1b[5m",
  reverse: "\x1b[7m",
  hidden: "\x1b[8m",
  
  fgBlack: "\x1b[30m",
  fgRed: "\x1b[31m",
  fgGreen: "\x1b[32m",
  fgYellow: "\x1b[33m",
  fgBlue: "\x1b[34m",
  fgMagenta: "\x1b[35m",
  fgCyan: "\x1b[36m",
  fgWhite: "\x1b[37m",
  
  bgBlack: "\x1b[40m",
  bgRed: "\x1b[41m",
  bgGreen: "\x1b[42m",
  bgYellow: "\x1b[43m",
  bgBlue: "\x1b[44m",
  bgMagenta: "\x1b[45m",
  bgCyan: "\x1b[46m",
  bgWhite: "\x1b[47m"
};

// Mock data generator utilities
const platforms = ["Telegram", "WhatsApp", "Instagram", "Instagram Story"];
const channels = ["@SpeedyNarcoticsIN", "@DirectMedsExpress", "@MedsExpress_IN", "@EcstasySupplies99", "@LSD_PartyStamps"];
const keywords = ["MDMA", "LSD", "Mephedrone", "Ecstasy", "party pills", "synthetic drugs"];
const locations = ["Delhi NCR", "Mumbai Metro", "Bengaluru", "Chennai", "Hyderabad", "Pune"];
const rawIps = ["103.45.210.4", "182.72.19.143", "202.164.44.82", "122.160.220.10"];
const isps = ["Bharti Airtel", "Reliance Jio", "Vodafone Idea", "ACT Fibernet"];
const botNames = ["@NarcoFastBot", "@DirectMedsBot", "@ExpressPillBot"];
const igNames = ["@GlowVibesParty", "@NightOutDeals", "@NeonTripsIndia"];
const phones = ["+91 98932 XXXXX", "+91 70008 XXXXX", "+91 88710 XXXXX"];
const texts = [
  "need party stamps for weekend dm for MDMA rates",
  "LSD blotters best quality imported available now",
  "ecstasy pills stocks refilled secure delivery",
  "Mephedrone rate card: 1g, 2g, 5g",
];

const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

let stats = {
  crawlers: 148,
  flagged: 1402,
  identities: 418,
  alerts: 92
};

let activeSim = null;

// ASCII Banner
function printBanner() {
  console.clear();
  console.log(`${Colors.fgYellow}${Colors.bright}`);
  console.log(" ██████╗  █████╗ ██╗  ██╗███████╗██╗  ██╗ █████╗ ███████╗████████╗██████╗  █████╗ ");
  console.log(" ██╔══██╗██╔══██╗██║ ██╔╝██╔════╝██║  ██║██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██╔══██╗");
  console.log(" ██████╔╝███████║█████╔╝ ███████╗███████║███████║███████╗   ██║   ██████╔╝███████║");
  console.log(" ██╔══██╗██╔══██║██╔═██╗ ╚════██║██╔══██║██╔══██║╚════██║   ██║   ██╔══██╗██╔══██║");
  console.log(" ██║  ██║██║  ██║██║  ██╗███████║██║  ██║██║  ██║███████║   ██║   ██║  ██║██║  ██║");
  console.log(" ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝");
  console.log(`\t\t      रक्षास्त्र — AUTONOMOUS SECURITY AGENT${Colors.reset}`);
  console.log(`${Colors.fgCyan}=============================================================================`);
  console.log(` Version: 1.0.0 | Status: NOMINAL | Node Version: ${process.version}`);
  console.log(`=============================================================================${Colors.reset}\n`);
}

// Stats Printer
function printStats() {
  console.log(`${Colors.fgWhite}${Colors.bright}--- SYSTEM METRICS ---${Colors.reset}`);
  console.log(` Active Crawlers:         ${Colors.fgCyan}${stats.crawlers}${Colors.reset}`);
  console.log(` Flagged Channels:        ${Colors.fgRed}${stats.flagged}${Colors.reset}`);
  console.log(` Mapped Identities:       ${Colors.fgYellow}${stats.identities}${Colors.reset}`);
  console.log(` Alerts Dispatched:       ${Colors.fgGreen}${stats.alerts}${Colors.reset}`);
  console.log(`${Colors.dim}----------------------${Colors.reset}\n`);
}

// Menu Options
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function showHelp() {
  console.log(`${Colors.fgWhite}${Colors.bright}Available Commands:${Colors.reset}`);
  console.log(`  ${Colors.fgCyan}stats${Colors.reset}     - Display current threat tracking numbers`);
  console.log(`  ${Colors.fgCyan}simulate${Colors.reset}  - Start real-time threat intelligence crawling logs`);
  console.log(`  ${Colors.fgCyan}help${Colors.reset}      - Show list of command controls`);
  console.log(`  ${Colors.fgCyan}exit${Colors.reset}      - Terminate agent program\n`);
}

async function startSimulation() {
  if (activeSim) {
    console.log(`${Colors.fgRed}Simulation is already running! Press Ctrl+C or type 'exit' to stop.${Colors.reset}\n`);
    return;
  }
  
  console.log(`${Colors.fgGreen}[+] Commencing crawler loops. Press Enter to pause/return to prompt...${Colors.reset}\n`);
  activeSim = true;

  // Readline hook to stop simulation on input
  const stopPromise = new Promise(resolve => {
    process.stdin.once("data", () => {
      activeSim = false;
      resolve();
    });
  });

  while (activeSim) {
    const idNum = Math.floor(Math.random() * 9000) + 1000;
    const postNum = Math.floor(Math.random() * 500) + 1;
    const confidence = (Math.random() * 15 + 85).toFixed(1);
    
    // Simulate multi-step intelligence log
    console.log(`${Colors.fgWhite}[CRAWLER]${Colors.reset} Spider #${idNum} scanning ${pick(platforms)}/${pick(channels)}...`);
    await delay(600);
    if (!activeSim) break;

    console.log(`${Colors.fgBlue}[NLP]${Colors.reset} Semantic analysis on content: "${Colors.dim}${pick(texts)}${Colors.reset}"`);
    await delay(800);
    if (!activeSim) break;

    if (Math.random() > 0.4) {
      console.log(`${Colors.fgRed}${Colors.bright}[ALERT] HIGH CONFIDENCE MATCH — Keyword: ${pick(keywords)} (${confidence}%)${Colors.reset}`);
      stats.flagged++;
      await delay(500);
      if (!activeSim) break;

      console.log(`${Colors.fgYellow}[TRIANGULATE]${Colors.reset} Resolving threat identity details...`);
      await delay(700);
      if (!activeSim) break;

      console.log(`${Colors.fgGreen}[SUCCESS]${Colors.reset} Triangulated: ${pick(locations)} | IP: ${pick(rawIps)} | ISP: ${pick(isps)}`);
      stats.identities++;
      await delay(600);
      if (!activeSim) break;

      console.log(`${Colors.fgBlue}[NEO4J GRAPH]${Colors.reset} Linking ${pick(botNames)} → ${pick(igNames)} via ${pick(phones)}`);
      stats.alerts++;
      console.log(`${Colors.fgGreen}[GATEWAY] Incident alert digest packet dispatched to LEA command centers.${Colors.reset}\n`);
      await delay(1000);
    } else {
      console.log(`${Colors.dim}[CRAWLER] No high-confidence keywords matched in post #${postNum}.${Colors.reset}\n`);
      await delay(1200);
    }
  }

  console.log(`\n${Colors.fgYellow}[!] Simulation paused. Returned to prompt.${Colors.reset}\n`);
}

function promptCommand() {
  rl.question(`${Colors.fgGreen}${Colors.bright}rakshastra@agent-core:~$ ${Colors.reset}`, async (cmd) => {
    const cleanCmd = cmd.trim().toLowerCase();
    
    if (cleanCmd === "exit") {
      console.log(`\n${Colors.fgRed}[!] Shutting down Rakshastra Agent... Offline.${Colors.reset}`);
      rl.close();
      process.exit(0);
    } else if (cleanCmd === "stats") {
      printStats();
    } else if (cleanCmd === "simulate") {
      await startSimulation();
    } else if (cleanCmd === "help" || cleanCmd === "?") {
      showHelp();
    } else if (cleanCmd === "") {
      // Just press enter
    } else {
      console.log(`${Colors.fgRed}Unknown command: "${cmd}". Type "help" for a list of commands.${Colors.reset}\n`);
    }
    promptCommand();
  });
}

// Entrypoint
printBanner();
showHelp();
promptCommand();
