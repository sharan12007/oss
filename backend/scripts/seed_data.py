"""
Seed script: loads a curated cancer-gene subset into Neo4j.
50 genes, their proteins, mutations, diseases, pathways, and relationships.
Run with: python -m scripts.seed_data
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import get_driver, write_query, close_driver
from app.schema import setup_schema
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# SEED DATA: Curated cancer / Alzheimer's gene subset
# ──────────────────────────────────────────────────────────────────────────────

GENES = [
    {"symbol": "BRCA1", "name": "BRCA1 DNA Repair Associated", "ensembl_id": "ENSG00000012048", "chromosome": "17q21.31"},
    {"symbol": "BRCA2", "name": "BRCA2 DNA Repair Associated", "ensembl_id": "ENSG00000139618", "chromosome": "13q13.1"},
    {"symbol": "TP53", "name": "Tumor Protein P53", "ensembl_id": "ENSG00000141510", "chromosome": "17p13.1"},
    {"symbol": "EGFR", "name": "Epidermal Growth Factor Receptor", "ensembl_id": "ENSG00000146648", "chromosome": "7p11.2"},
    {"symbol": "KRAS", "name": "KRAS Proto-Oncogene GTPase", "ensembl_id": "ENSG00000133703", "chromosome": "12p12.1"},
    {"symbol": "BRAF", "name": "B-Raf Proto-Oncogene Serine/Threonine Kinase", "ensembl_id": "ENSG00000157764", "chromosome": "7q34"},
    {"symbol": "PIK3CA", "name": "Phosphatidylinositol-4,5-Bisphosphate 3-Kinase Catalytic Subunit Alpha", "ensembl_id": "ENSG00000121879", "chromosome": "3q26.32"},
    {"symbol": "PTEN", "name": "Phosphatase and Tensin Homolog", "ensembl_id": "ENSG00000171862", "chromosome": "10q23.31"},
    {"symbol": "AKT1", "name": "AKT Serine/Threonine Kinase 1", "ensembl_id": "ENSG00000142208", "chromosome": "14q32.33"},
    {"symbol": "MTOR", "name": "Mechanistic Target of Rapamycin Kinase", "ensembl_id": "ENSG00000198793", "chromosome": "1p36.22"},
    {"symbol": "MYC", "name": "MYC Proto-Oncogene BHLH Transcription Factor", "ensembl_id": "ENSG00000136997", "chromosome": "8q24.21"},
    {"symbol": "RB1", "name": "RB Transcriptional Corepressor 1", "ensembl_id": "ENSG00000139687", "chromosome": "13q14.2"},
    {"symbol": "APC", "name": "APC Regulator of WNT Signaling Pathway", "ensembl_id": "ENSG00000134982", "chromosome": "5q22.2"},
    {"symbol": "VHL", "name": "Von Hippel-Lindau Tumor Suppressor", "ensembl_id": "ENSG00000134086", "chromosome": "3p25.3"},
    {"symbol": "ERBB2", "name": "Erb-B2 Receptor Tyrosine Kinase 2", "ensembl_id": "ENSG00000141736", "chromosome": "17q12"},
    {"symbol": "ALK", "name": "ALK Receptor Tyrosine Kinase", "ensembl_id": "ENSG00000171094", "chromosome": "2p23.2-p23.1"},
    {"symbol": "RET", "name": "Ret Proto-Oncogene", "ensembl_id": "ENSG00000165731", "chromosome": "10q11.21"},
    {"symbol": "MET", "name": "MET Proto-Oncogene Receptor Tyrosine Kinase", "ensembl_id": "ENSG00000105976", "chromosome": "7q31.2"},
    {"symbol": "CDH1", "name": "Cadherin 1", "ensembl_id": "ENSG00000039068", "chromosome": "16q22.1"},
    {"symbol": "PALB2", "name": "Partner and Localizer of BRCA2", "ensembl_id": "ENSG00000083093", "chromosome": "16p12.2"},
    {"symbol": "ATM", "name": "ATM Serine/Threonine Kinase", "ensembl_id": "ENSG00000149311", "chromosome": "11q22.3"},
    {"symbol": "CHEK2", "name": "Checkpoint Kinase 2", "ensembl_id": "ENSG00000183765", "chromosome": "22q12.1"},
    {"symbol": "MLH1", "name": "MutL Homolog 1", "ensembl_id": "ENSG00000076242", "chromosome": "3p21.3"},
    {"symbol": "MSH2", "name": "MutS Homolog 2", "ensembl_id": "ENSG00000095002", "chromosome": "2p21-p16.3"},
    {"symbol": "JAK2", "name": "Janus Kinase 2", "ensembl_id": "ENSG00000096968", "chromosome": "9p24.1"},
    {"symbol": "NRAS", "name": "NRAS Proto-Oncogene GTPase", "ensembl_id": "ENSG00000213281", "chromosome": "1p13.2"},
    {"symbol": "HRAS", "name": "HRas Proto-Oncogene GTPase", "ensembl_id": "ENSG00000174775", "chromosome": "11p15.5"},
    {"symbol": "RAF1", "name": "Raf-1 Proto-Oncogene Serine/Threonine Kinase", "ensembl_id": "ENSG00000132155", "chromosome": "3p25.2"},
    {"symbol": "MAP2K1", "name": "Mitogen-Activated Protein Kinase Kinase 1", "ensembl_id": "ENSG00000169032", "chromosome": "15q22.31"},
    {"symbol": "MAPK1", "name": "Mitogen-Activated Protein Kinase 1", "ensembl_id": "ENSG00000100030", "chromosome": "22q11.22"},
    # Alzheimer's-related genes
    {"symbol": "APP", "name": "Amyloid Beta Precursor Protein", "ensembl_id": "ENSG00000142192", "chromosome": "21q21.3"},
    {"symbol": "PSEN1", "name": "Presenilin 1", "ensembl_id": "ENSG00000080815", "chromosome": "14q24.2"},
    {"symbol": "PSEN2", "name": "Presenilin 2", "ensembl_id": "ENSG00000143801", "chromosome": "1q42.13"},
    {"symbol": "APOE", "name": "Apolipoprotein E", "ensembl_id": "ENSG00000130203", "chromosome": "19q13.32"},
    {"symbol": "TREM2", "name": "Triggering Receptor Expressed on Myeloid Cells 2", "ensembl_id": "ENSG00000095970", "chromosome": "6p21.1"},
    {"symbol": "MAPT", "name": "Microtubule Associated Protein Tau", "ensembl_id": "ENSG00000186868", "chromosome": "17q21.31"},
    {"symbol": "ABCA7", "name": "ATP Binding Cassette Subfamily A Member 7", "ensembl_id": "ENSG00000064687", "chromosome": "19p13.3"},
    {"symbol": "CLU", "name": "Clusterin", "ensembl_id": "ENSG00000120885", "chromosome": "8p21.1"},
    {"symbol": "SORL1", "name": "Sortilin Related Receptor 1", "ensembl_id": "ENSG00000137642", "chromosome": "11q24.1"},
    {"symbol": "BIN1", "name": "Bridging Integrator 1", "ensembl_id": "ENSG00000136717", "chromosome": "2q14.3"},
    # Additional cancer genes
    {"symbol": "CDKN2A", "name": "Cyclin Dependent Kinase Inhibitor 2A", "ensembl_id": "ENSG00000147889", "chromosome": "9p21.3"},
    {"symbol": "STK11", "name": "Serine/Threonine Kinase 11", "ensembl_id": "ENSG00000118046", "chromosome": "19p13.3"},
    {"symbol": "SMAD4", "name": "SMAD Family Member 4", "ensembl_id": "ENSG00000141646", "chromosome": "18q21.2"},
    {"symbol": "IDH1", "name": "Isocitrate Dehydrogenase (NADP+) 1", "ensembl_id": "ENSG00000138413", "chromosome": "2q34"},
    {"symbol": "IDH2", "name": "Isocitrate Dehydrogenase (NADP+) 2", "ensembl_id": "ENSG00000182054", "chromosome": "15q26.1"},
    {"symbol": "FGFR2", "name": "Fibroblast Growth Factor Receptor 2", "ensembl_id": "ENSG00000066468", "chromosome": "10q26.13"},
    {"symbol": "FGFR3", "name": "Fibroblast Growth Factor Receptor 3", "ensembl_id": "ENSG00000068078", "chromosome": "4p16.3"},
    {"symbol": "KIT", "name": "KIT Proto-Oncogene Receptor Tyrosine Kinase", "ensembl_id": "ENSG00000157404", "chromosome": "4q12"},
    {"symbol": "PDGFRA", "name": "Platelet Derived Growth Factor Receptor Alpha", "ensembl_id": "ENSG00000134853", "chromosome": "4q12"},
    {"symbol": "FLT3", "name": "Fms Related Receptor Tyrosine Kinase 3", "ensembl_id": "ENSG00000122025", "chromosome": "13q12.2"},
]

PROTEINS = [
    {"uniprot_id": "P38398", "name": "Breast cancer type 1 susceptibility protein", "function": "E3 ubiquitin-protein ligase; DNA repair", "gene": "BRCA1"},
    {"uniprot_id": "P51587", "name": "Breast cancer type 2 susceptibility protein", "function": "Double-strand break repair via homologous recombination", "gene": "BRCA2"},
    {"uniprot_id": "P04637", "name": "Cellular tumor antigen p53", "function": "Tumor suppressor; transcription factor; apoptosis", "gene": "TP53"},
    {"uniprot_id": "P00533", "name": "Epidermal growth factor receptor", "function": "Receptor tyrosine kinase; cell proliferation signaling", "gene": "EGFR"},
    {"uniprot_id": "P01116", "name": "GTPase KRas", "function": "GTPase; RAS-MAPK signaling", "gene": "KRAS"},
    {"uniprot_id": "P15056", "name": "Serine/threonine-protein kinase B-raf", "function": "MAP kinase signaling; cell growth", "gene": "BRAF"},
    {"uniprot_id": "P42336", "name": "PI3-kinase subunit alpha", "function": "Phosphoinositide 3-kinase; PI3K-AKT signaling", "gene": "PIK3CA"},
    {"uniprot_id": "P60484", "name": "Phosphatidylinositol 3,4,5-trisphosphate 3-phosphatase", "function": "Tumor suppressor phosphatase; PI3K-AKT inhibition", "gene": "PTEN"},
    {"uniprot_id": "P31749", "name": "RAC-alpha serine/threonine-protein kinase", "function": "Serine/threonine kinase; cell survival signaling", "gene": "AKT1"},
    {"uniprot_id": "P42345", "name": "Serine/threonine-protein kinase mTOR", "function": "Central regulator of cell growth and autophagy", "gene": "MTOR"},
    {"uniprot_id": "P01106", "name": "Myc proto-oncogene protein", "function": "Transcription factor; cell cycle progression", "gene": "MYC"},
    {"uniprot_id": "P06400", "name": "Retinoblastoma-associated protein", "function": "Tumor suppressor; cell cycle regulation", "gene": "RB1"},
    {"uniprot_id": "P25054", "name": "Adenomatous polyposis coli protein", "function": "Tumor suppressor; WNT signaling regulation", "gene": "APC"},
    {"uniprot_id": "P40337", "name": "Von Hippel-Lindau disease tumor suppressor", "function": "E3 ubiquitin ligase; HIF regulation", "gene": "VHL"},
    {"uniprot_id": "P04626", "name": "Receptor tyrosine-protein kinase erbB-2", "function": "Receptor tyrosine kinase; cell proliferation", "gene": "ERBB2"},
    {"uniprot_id": "Q9UM73", "name": "ALK tyrosine kinase receptor", "function": "Receptor tyrosine kinase; neural development", "gene": "ALK"},
    {"uniprot_id": "P07949", "name": "Proto-oncogene tyrosine-protein kinase receptor Ret", "function": "Receptor tyrosine kinase; neural crest development", "gene": "RET"},
    {"uniprot_id": "P08581", "name": "Hepatocyte growth factor receptor", "function": "Receptor tyrosine kinase; cell motility and growth", "gene": "MET"},
    {"uniprot_id": "P12830", "name": "Cadherin-1", "function": "Cell-cell adhesion glycoprotein", "gene": "CDH1"},
    {"uniprot_id": "Q86YC2", "name": "Partner and localizer of BRCA2", "function": "BRCA2 nuclear localization; DNA repair", "gene": "PALB2"},
    {"uniprot_id": "Q13315", "name": "Serine-protein kinase ATM", "function": "DNA damage checkpoint kinase", "gene": "ATM"},
    {"uniprot_id": "O96017", "name": "Serine/threonine-protein kinase Chk2", "function": "Cell cycle checkpoint kinase", "gene": "CHEK2"},
    {"uniprot_id": "P40692", "name": "DNA mismatch repair protein Mlh1", "function": "Mismatch repair; microsatellite stability", "gene": "MLH1"},
    {"uniprot_id": "P43246", "name": "DNA mismatch repair protein Msh2", "function": "Mismatch recognition in DNA repair", "gene": "MSH2"},
    {"uniprot_id": "O60674", "name": "Tyrosine-protein kinase JAK2", "function": "JAK-STAT signaling; hematopoiesis", "gene": "JAK2"},
    {"uniprot_id": "P05062", "name": "Amyloid-beta precursor protein", "function": "Cell surface receptor; neural plasticity", "gene": "APP"},
    {"uniprot_id": "P49768", "name": "Presenilin-1", "function": "Gamma-secretase complex subunit; APP processing", "gene": "PSEN1"},
    {"uniprot_id": "P49810", "name": "Presenilin-2", "function": "Gamma-secretase complex subunit", "gene": "PSEN2"},
    {"uniprot_id": "P02649", "name": "Apolipoprotein E", "function": "Lipid transport; cholesterol metabolism", "gene": "APOE"},
    {"uniprot_id": "Q9NZC2", "name": "Triggering receptor expressed on myeloid cells 2", "function": "Innate immunity; microglial function", "gene": "TREM2"},
    {"uniprot_id": "P10636", "name": "Microtubule-associated protein tau", "function": "Microtubule assembly and stabilization", "gene": "MAPT"},
]

DISEASES = [
    {"id": "DOID:1612", "name": "Breast Cancer", "description": "A thorax cancer that originates in the mammary gland."},
    {"id": "DOID:10283", "name": "Prostate Cancer", "description": "A male reproductive organ cancer in the prostate gland."},
    {"id": "DOID:9256", "name": "Colorectal Cancer", "description": "A large intestine cancer that originates in the colon or rectum."},
    {"id": "DOID:3908", "name": "Non-Small Cell Lung Cancer", "description": "A lung non-small cell carcinoma."},
    {"id": "DOID:4362", "name": "Cervical Cancer", "description": "A female reproductive organ cancer in the cervix."},
    {"id": "DOID:1781", "name": "Thyroid Cancer", "description": "An endocrine gland cancer in the thyroid gland."},
    {"id": "DOID:2394", "name": "Ovarian Cancer", "description": "A female reproductive organ cancer in the ovary."},
    {"id": "DOID:4159", "name": "Skin Melanoma", "description": "A skin cancer originating from melanocytes."},
    {"id": "DOID:3856", "name": "Renal Cell Carcinoma", "description": "A kidney cancer originating from renal tubule cells."},
    {"id": "DOID:9119", "name": "Acute Myeloid Leukemia", "description": "A myeloid leukemia characterized by rapid growth of abnormal white blood cells."},
    {"id": "DOID:10652", "name": "Alzheimer's Disease", "description": "A neurodegenerative tauopathy characterized by progressive memory loss and cognitive decline."},
    {"id": "DOID:14330", "name": "Parkinson's Disease", "description": "A neurodegenerative disease affecting motor function."},
    {"id": "DOID:5419", "name": "Glioblastoma", "description": "A malignant brain tumor from glial cells."},
    {"id": "DOID:1324", "name": "Lung Cancer", "description": "A respiratory system cancer originating in the lung."},
    {"id": "DOID:2596", "name": "Gastric Cancer", "description": "A stomach cancer."},
    {"id": "DOID:263", "name": "Kidney Cancer", "description": "A urinary system cancer in the kidney."},
    {"id": "DOID:8552", "name": "Chronic Myeloid Leukemia", "description": "A chronic myelogenous leukemia characterized by BCR-ABL fusion."},
    {"id": "DOID:1909", "name": "Melanoma", "description": "A cell type cancer originating from melanocytes."},
    {"id": "DOID:10534", "name": "Stomach Cancer", "description": "A gastrointestinal cancer in the stomach."},
    {"id": "DOID:684", "name": "Hepatocellular Carcinoma", "description": "A liver cancer from hepatocytes."},
    {"id": "DOID:3571", "name": "Li-Fraumeni Syndrome", "description": "A hereditary cancer predisposition syndrome caused by TP53 mutations."},
    {"id": "DOID:0050742", "name": "Lynch Syndrome", "description": "A hereditary nonpolyposis colorectal cancer syndrome."},
]

PATHWAYS = [
    {"reactome_id": "R-HSA-1640170", "name": "Cell Cycle"},
    {"reactome_id": "R-HSA-5357801", "name": "Programmed Cell Death (Apoptosis)"},
    {"reactome_id": "R-HSA-9006934", "name": "Signaling by Receptor Tyrosine Kinases"},
    {"reactome_id": "R-HSA-2219528", "name": "PI3K/AKT Signaling in Cancer"},
    {"reactome_id": "R-HSA-6802957", "name": "Oncogene Induced Senescence"},
    {"reactome_id": "R-HSA-5358351", "name": "Signaling by RAS Mutants"},
    {"reactome_id": "R-HSA-73887", "name": "Death Receptor Signaling"},
    {"reactome_id": "R-HSA-5683057", "name": "MAPK Family Signaling Cascades"},
    {"reactome_id": "R-HSA-195721", "name": "Signaling by WNT"},
    {"reactome_id": "R-HSA-2262752", "name": "Cellular Responses to Stress"},
    {"reactome_id": "R-HSA-69278", "name": "Cell Cycle, Mitotic"},
    {"reactome_id": "R-HSA-73857", "name": "RNA Polymerase II Transcription"},
    {"reactome_id": "R-HSA-5663202", "name": "Diseases of Signal Transduction by Growth Factor Receptors"},
    {"reactome_id": "R-HSA-69620", "name": "Cell Cycle Checkpoints"},
    {"reactome_id": "R-HSA-1280218", "name": "Adaptive Immune System"},
    {"reactome_id": "R-HSA-168256", "name": "Immune System"},
    {"reactome_id": "R-HSA-392499", "name": "Metabolism of Proteins"},
    {"reactome_id": "R-HSA-9609507", "name": "Protein Localization"},
    {"reactome_id": "R-HSA-422475", "name": "Axon Guidance"},
    {"reactome_id": "R-HSA-9716542", "name": "Signaling by NTRK1 (TRKA)"},
]

MUTATIONS = [
    {"id": "CV-17661", "hgvs": "NM_007294.4:c.5266dupC", "type": "Insertion", "clinical_significance": "Pathogenic", "gene": "BRCA1"},
    {"id": "CV-55370", "hgvs": "NM_007294.4:c.68_69delAG", "type": "Deletion", "clinical_significance": "Pathogenic", "gene": "BRCA1"},
    {"id": "CV-38077", "hgvs": "NM_000059.4:c.5946delT", "type": "Deletion", "clinical_significance": "Pathogenic", "gene": "BRCA2"},
    {"id": "CV-52051", "hgvs": "NM_000546.6:c.743G>A (p.Arg248Gln)", "type": "SNV", "clinical_significance": "Pathogenic", "gene": "TP53"},
    {"id": "CV-52052", "hgvs": "NM_000546.6:c.818G>A (p.Arg273His)", "type": "SNV", "clinical_significance": "Pathogenic", "gene": "TP53"},
    {"id": "CV-16609", "hgvs": "NM_005228.5:c.2573T>G (p.Leu858Arg)", "type": "SNV", "clinical_significance": "Pathogenic", "gene": "EGFR"},
    {"id": "CV-12582", "hgvs": "NM_004985.5:c.35G>T (p.Gly12Val)", "type": "SNV", "clinical_significance": "Pathogenic", "gene": "KRAS"},
    {"id": "CV-13961", "hgvs": "NM_004333.6:c.1799T>A (p.Val600Glu)", "type": "SNV", "clinical_significance": "Pathogenic", "gene": "BRAF"},
    {"id": "CV-18955", "hgvs": "NM_006218.4:c.3140A>G (p.His1047Arg)", "type": "SNV", "clinical_significance": "Pathogenic", "gene": "PIK3CA"},
    {"id": "CV-3676", "hgvs": "NM_000314.8:c.388C>T (p.Arg130Ter)", "type": "SNV", "clinical_significance": "Pathogenic", "gene": "PTEN"},
    {"id": "CV-404226", "hgvs": "NM_004343.4:c.34G>T (p.Val617Phe)", "type": "SNV", "clinical_significance": "Pathogenic", "gene": "JAK2"},
    {"id": "CV-AD001", "hgvs": "NM_000484.4:c.2149G>A (p.Val717Ile)", "type": "SNV", "clinical_significance": "Pathogenic", "gene": "APP"},
    {"id": "CV-AD002", "hgvs": "NM_000021.4:c.868A>G (p.Met292Val)", "type": "SNV", "clinical_significance": "Pathogenic", "gene": "PSEN1"},
    {"id": "CV-MLH1", "hgvs": "NM_000249.4:c.350C>T (p.Thr117Met)", "type": "SNV", "clinical_significance": "Pathogenic", "gene": "MLH1"},
    {"id": "CV-MSH2", "hgvs": "NM_000251.3:c.942+3A>T", "type": "SNV", "clinical_significance": "Pathogenic", "gene": "MSH2"},
]

# Gene -> Disease associations with scores
GENE_DISEASE_ASSOCIATIONS = [
    ("BRCA1", "DOID:1612", 0.95),  # Breast Cancer
    ("BRCA1", "DOID:2394", 0.85),  # Ovarian Cancer
    ("BRCA2", "DOID:1612", 0.93),  # Breast Cancer
    ("BRCA2", "DOID:10283", 0.72),  # Prostate Cancer
    ("BRCA2", "DOID:2394", 0.80),  # Ovarian Cancer
    ("TP53", "DOID:1612", 0.88),   # Breast Cancer
    ("TP53", "DOID:3571", 0.97),   # Li-Fraumeni Syndrome
    ("TP53", "DOID:9256", 0.82),   # Colorectal Cancer
    ("TP53", "DOID:1324", 0.85),   # Lung Cancer
    ("TP53", "DOID:5419", 0.78),   # Glioblastoma
    ("EGFR", "DOID:3908", 0.92),   # Non-Small Cell Lung Cancer
    ("EGFR", "DOID:5419", 0.80),   # Glioblastoma
    ("KRAS", "DOID:9256", 0.90),   # Colorectal Cancer
    ("KRAS", "DOID:3908", 0.88),   # NSCLC
    ("KRAS", "DOID:684", 0.70),    # Hepatocellular Carcinoma
    ("BRAF", "DOID:4159", 0.93),   # Skin Melanoma
    ("BRAF", "DOID:9256", 0.78),   # Colorectal Cancer
    ("BRAF", "DOID:1781", 0.82),   # Thyroid Cancer
    ("PIK3CA", "DOID:1612", 0.80),  # Breast Cancer
    ("PIK3CA", "DOID:9256", 0.72),  # Colorectal Cancer
    ("PTEN", "DOID:1612", 0.78),   # Breast Cancer
    ("PTEN", "DOID:5419", 0.82),   # Glioblastoma
    ("PTEN", "DOID:10283", 0.75),  # Prostate Cancer
    ("ERBB2", "DOID:1612", 0.90),  # Breast Cancer
    ("ERBB2", "DOID:2596", 0.70),  # Gastric Cancer
    ("ALK", "DOID:3908", 0.85),    # NSCLC
    ("RET", "DOID:1781", 0.88),    # Thyroid Cancer
    ("MET", "DOID:3908", 0.72),    # NSCLC
    ("MET", "DOID:684", 0.68),     # Hepatocellular Carcinoma
    ("CDH1", "DOID:2596", 0.80),   # Gastric Cancer
    ("CDH1", "DOID:1612", 0.65),   # Breast Cancer
    ("PALB2", "DOID:1612", 0.82),  # Breast Cancer
    ("ATM", "DOID:1612", 0.70),    # Breast Cancer
    ("CHEK2", "DOID:1612", 0.68),  # Breast Cancer
    ("MLH1", "DOID:9256", 0.90),   # Colorectal Cancer
    ("MLH1", "DOID:0050742", 0.95),# Lynch Syndrome
    ("MSH2", "DOID:9256", 0.88),   # Colorectal Cancer
    ("MSH2", "DOID:0050742", 0.93),# Lynch Syndrome
    ("JAK2", "DOID:8552", 0.90),   # Chronic Myeloid Leukemia
    ("JAK2", "DOID:9119", 0.80),   # Acute Myeloid Leukemia
    ("VHL", "DOID:3856", 0.92),    # Renal Cell Carcinoma
    ("APC", "DOID:9256", 0.95),    # Colorectal Cancer
    ("RB1", "DOID:1324", 0.75),    # Lung Cancer
    ("MYC", "DOID:1612", 0.72),    # Breast Cancer
    ("MYC", "DOID:9119", 0.78),    # AML
    ("IDH1", "DOID:5419", 0.85),   # Glioblastoma
    ("IDH1", "DOID:9119", 0.78),   # AML
    ("IDH2", "DOID:9119", 0.82),   # AML
    ("FLT3", "DOID:9119", 0.90),   # AML
    ("KIT", "DOID:9119", 0.75),    # AML
    ("FGFR2", "DOID:1612", 0.60),  # Breast Cancer
    ("FGFR3", "DOID:263", 0.72),   # Kidney Cancer
    # Alzheimer's associations
    ("APP", "DOID:10652", 0.96),    # Alzheimer's
    ("PSEN1", "DOID:10652", 0.97),  # Alzheimer's
    ("PSEN2", "DOID:10652", 0.88),  # Alzheimer's
    ("APOE", "DOID:10652", 0.95),   # Alzheimer's
    ("TREM2", "DOID:10652", 0.82),  # Alzheimer's
    ("MAPT", "DOID:10652", 0.85),   # Alzheimer's
    ("MAPT", "DOID:14330", 0.70),   # Parkinson's
    ("ABCA7", "DOID:10652", 0.72),  # Alzheimer's
    ("CLU", "DOID:10652", 0.68),    # Alzheimer's
    ("SORL1", "DOID:10652", 0.75),  # Alzheimer's
    ("BIN1", "DOID:10652", 0.70),   # Alzheimer's
]

# Protein-protein interactions (gene symbols for simplicity, will be resolved)
PROTEIN_INTERACTIONS = [
    ("BRCA1", "BRCA2", 0.95),
    ("BRCA1", "TP53", 0.90),
    ("BRCA1", "ATM", 0.88),
    ("BRCA1", "CHEK2", 0.82),
    ("BRCA1", "PALB2", 0.93),
    ("BRCA2", "PALB2", 0.96),
    ("TP53", "RB1", 0.85),
    ("TP53", "MYC", 0.80),
    ("TP53", "PTEN", 0.78),
    ("EGFR", "ERBB2", 0.90),
    ("EGFR", "KRAS", 0.82),
    ("EGFR", "MET", 0.75),
    ("KRAS", "BRAF", 0.95),
    ("KRAS", "RAF1", 0.90),
    ("KRAS", "NRAS", 0.85),
    ("BRAF", "MAP2K1", 0.92),
    ("MAP2K1", "MAPK1", 0.95),
    ("PIK3CA", "AKT1", 0.93),
    ("PIK3CA", "PTEN", 0.88),
    ("AKT1", "MTOR", 0.90),
    ("PTEN", "AKT1", 0.85),
    ("MLH1", "MSH2", 0.95),
    ("APP", "PSEN1", 0.92),
    ("APP", "PSEN2", 0.85),
    ("PSEN1", "PSEN2", 0.90),
    ("MAPT", "APP", 0.70),
    ("APOE", "APP", 0.78),
    ("APOE", "TREM2", 0.65),
    ("TREM2", "APP", 0.60),
    ("CLU", "APOE", 0.72),
]

# Gene -> Pathway associations
GENE_PATHWAY = [
    ("BRCA1", "R-HSA-69620"),    # Cell Cycle Checkpoints
    ("BRCA1", "R-HSA-2262752"),  # Cellular Responses to Stress
    ("TP53", "R-HSA-5357801"),   # Apoptosis
    ("TP53", "R-HSA-1640170"),   # Cell Cycle
    ("TP53", "R-HSA-6802957"),   # Oncogene Induced Senescence
    ("EGFR", "R-HSA-9006934"),   # RTK Signaling
    ("EGFR", "R-HSA-5683057"),   # MAPK Cascades
    ("EGFR", "R-HSA-5663202"),   # Diseases of Signal Transduction
    ("KRAS", "R-HSA-5358351"),   # RAS Mutant Signaling
    ("KRAS", "R-HSA-5683057"),   # MAPK Cascades
    ("BRAF", "R-HSA-5683057"),   # MAPK Cascades
    ("BRAF", "R-HSA-5358351"),   # RAS Mutant Signaling
    ("PIK3CA", "R-HSA-2219528"),# PI3K/AKT Signaling
    ("PTEN", "R-HSA-2219528"),  # PI3K/AKT Signaling
    ("AKT1", "R-HSA-2219528"),  # PI3K/AKT Signaling
    ("MTOR", "R-HSA-2219528"),  # PI3K/AKT Signaling
    ("MYC", "R-HSA-73857"),     # RNA Pol II Transcription
    ("RB1", "R-HSA-1640170"),   # Cell Cycle
    ("APC", "R-HSA-195721"),    # WNT Signaling
    ("MAP2K1", "R-HSA-5683057"),# MAPK Cascades
    ("MAPK1", "R-HSA-5683057"), # MAPK Cascades
    ("ALK", "R-HSA-9006934"),   # RTK Signaling
    ("RET", "R-HSA-9006934"),   # RTK Signaling
    ("MET", "R-HSA-9006934"),   # RTK Signaling
    ("ERBB2", "R-HSA-9006934"), # RTK Signaling
    ("ERBB2", "R-HSA-5663202"), # Diseases of Signal Transduction
    ("JAK2", "R-HSA-168256"),   # Immune System
    ("TREM2", "R-HSA-1280218"), # Adaptive Immune System
    ("MAPT", "R-HSA-422475"),   # Axon Guidance
    ("APP", "R-HSA-392499"),    # Metabolism of Proteins
    ("PSEN1", "R-HSA-392499"),  # Metabolism of Proteins
    ("FLT3", "R-HSA-9006934"),  # RTK Signaling
    ("KIT", "R-HSA-9006934"),   # RTK Signaling
    ("PDGFRA", "R-HSA-9006934"),# RTK Signaling
    ("FGFR2", "R-HSA-9006934"), # RTK Signaling
    ("FGFR3", "R-HSA-9006934"), # RTK Signaling
]

# Mutation -> Disease links
MUTATION_DISEASE = [
    ("CV-17661", "DOID:1612"),   # BRCA1 5382insC -> Breast Cancer
    ("CV-17661", "DOID:2394"),   # BRCA1 5382insC -> Ovarian Cancer
    ("CV-55370", "DOID:1612"),   # BRCA1 185delAG -> Breast Cancer
    ("CV-38077", "DOID:1612"),   # BRCA2 -> Breast Cancer
    ("CV-52051", "DOID:3571"),   # TP53 R248Q -> Li-Fraumeni
    ("CV-52052", "DOID:3571"),   # TP53 R273H -> Li-Fraumeni
    ("CV-16609", "DOID:3908"),   # EGFR L858R -> NSCLC
    ("CV-12582", "DOID:9256"),   # KRAS G12V -> Colorectal
    ("CV-12582", "DOID:3908"),   # KRAS G12V -> NSCLC
    ("CV-13961", "DOID:4159"),   # BRAF V600E -> Melanoma
    ("CV-13961", "DOID:1781"),   # BRAF V600E -> Thyroid
    ("CV-18955", "DOID:1612"),   # PIK3CA H1047R -> Breast Cancer
    ("CV-3676", "DOID:5419"),    # PTEN -> Glioblastoma
    ("CV-404226", "DOID:8552"),  # JAK2 V617F -> CML
    ("CV-AD001", "DOID:10652"),  # APP V717I -> Alzheimer's
    ("CV-AD002", "DOID:10652"),  # PSEN1 M292V -> Alzheimer's
    ("CV-MLH1", "DOID:0050742"), # MLH1 -> Lynch Syndrome
    ("CV-MSH2", "DOID:0050742"), # MSH2 -> Lynch Syndrome
]

# Sample publications
PUBLICATIONS = [
    {"pmid": "20301425", "title": "Comprehensive genomic characterization defines human glioblastoma genes and core pathways", "abstract": "Comprehensive genomic analysis of glioblastoma multiforme identifies genes and pathways frequently altered in this cancer.", "year": 2008},
    {"pmid": "23000897", "title": "Comprehensive molecular portraits of human breast tumours", "abstract": "The Cancer Genome Atlas analysis of breast cancer establishes four main genomic subtypes.", "year": 2012},
    {"pmid": "25079552", "title": "Comprehensive molecular characterization of gastric adenocarcinoma", "abstract": "TCGA characterization of gastric cancer identifies four distinct molecular subtypes.", "year": 2014},
    {"pmid": "26000487", "title": "The molecular taxonomy of primary prostate cancer", "abstract": "Comprehensive molecular analysis of prostate cancer identifies distinct subtypes.", "year": 2015},
    {"pmid": "32123317", "title": "Genetics of Alzheimer's disease: a centennial review", "abstract": "Review of genetic discoveries in Alzheimer's disease over the past century, including APP, PSEN1, PSEN2, and APOE.", "year": 2020},
]

# Publication -> Entity mentions
PUB_MENTIONS = [
    ("20301425", ["TP53", "EGFR", "PTEN", "IDH1"], ["DOID:5419"]),
    ("23000897", ["BRCA1", "BRCA2", "TP53", "PIK3CA", "ERBB2"], ["DOID:1612"]),
    ("25079552", ["CDH1", "ERBB2", "KRAS"], ["DOID:2596"]),
    ("26000487", ["BRCA2", "PTEN", "TP53"], ["DOID:10283"]),
    ("32123317", ["APP", "PSEN1", "PSEN2", "APOE", "TREM2", "MAPT", "CLU", "BIN1", "ABCA7", "SORL1"], ["DOID:10652"]),
]


async def seed_all():
    """Run the full seed pipeline."""
    await setup_schema()

    logger.info("Seeding genes...")
    for g in GENES:
        await write_query(
            """MERGE (g:Gene {symbol: $symbol})
               SET g.name = $name, g.ensembl_id = $ensembl_id, g.chromosome = $chromosome""",
            g,
        )

    logger.info("Seeding proteins...")
    for p in PROTEINS:
        gene = p.pop("gene")
        await write_query(
            """MERGE (p:Protein {uniprot_id: $uniprot_id})
               SET p.name = $name, p.function = $function
               WITH p
               MATCH (g:Gene {symbol: $gene})
               MERGE (g)-[:ENCODES]->(p)""",
            {**p, "gene": gene},
        )
        p["gene"] = gene  # restore

    logger.info("Seeding diseases...")
    for d in DISEASES:
        await write_query(
            """MERGE (d:Disease {id: $id})
               SET d.name = $name, d.description = $description""",
            d,
        )

    logger.info("Seeding pathways...")
    for pw in PATHWAYS:
        await write_query(
            """MERGE (pw:Pathway {reactome_id: $reactome_id})
               SET pw.name = $name""",
            pw,
        )

    logger.info("Seeding mutations...")
    for m in MUTATIONS:
        gene = m.pop("gene")
        await write_query(
            """MERGE (m:Mutation {id: $id})
               SET m.hgvs = $hgvs, m.type = $type, m.clinical_significance = $clinical_significance
               WITH m
               MATCH (g:Gene {symbol: $gene})
               MERGE (g)-[:HAS_MUTATION]->(m)""",
            {**m, "gene": gene},
        )
        m["gene"] = gene  # restore

    logger.info("Seeding gene-disease associations...")
    for gene_sym, disease_id, score in GENE_DISEASE_ASSOCIATIONS:
        await write_query(
            """MATCH (g:Gene {symbol: $gene}), (d:Disease {id: $disease})
               MERGE (g)-[:ASSOCIATED_WITH {score: $score}]->(d)""",
            {"gene": gene_sym, "disease": disease_id, "score": score},
        )

    logger.info("Seeding protein-protein interactions...")
    for g1, g2, score in PROTEIN_INTERACTIONS:
        await write_query(
            """MATCH (g1:Gene {symbol: $g1})-[:ENCODES]->(p1:Protein),
                     (g2:Gene {symbol: $g2})-[:ENCODES]->(p2:Protein)
               MERGE (p1)-[:INTERACTS_WITH {score: $score}]->(p2)""",
            {"g1": g1, "g2": g2, "score": score},
        )

    logger.info("Seeding gene-pathway associations...")
    for gene_sym, pathway_id in GENE_PATHWAY:
        await write_query(
            """MATCH (g:Gene {symbol: $gene})-[:ENCODES]->(p:Protein),
                     (pw:Pathway {reactome_id: $pathway})
               MERGE (p)-[:PART_OF]->(pw)""",
            {"gene": gene_sym, "pathway": pathway_id},
        )

    logger.info("Seeding mutation-disease links...")
    for mut_id, disease_id in MUTATION_DISEASE:
        await write_query(
            """MATCH (m:Mutation {id: $mut}), (d:Disease {id: $disease})
               MERGE (m)-[:LINKED_TO]->(d)""",
            {"mut": mut_id, "disease": disease_id},
        )

    logger.info("Seeding publications...")
    for pub in PUBLICATIONS:
        await write_query(
            """MERGE (pub:Publication {pmid: $pmid})
               SET pub.title = $title, pub.abstract = $abstract, pub.year = $year""",
            pub,
        )

    logger.info("Seeding publication mentions...")
    for pmid, genes, diseases in PUB_MENTIONS:
        for gene_sym in genes:
            await write_query(
                """MATCH (pub:Publication {pmid: $pmid}), (g:Gene {symbol: $gene})
                   MERGE (pub)-[:MENTIONS]->(g)""",
                {"pmid": pmid, "gene": gene_sym},
            )
        for disease_id in diseases:
            await write_query(
                """MATCH (pub:Publication {pmid: $pmid}), (d:Disease {id: $disease})
                   MERGE (pub)-[:MENTIONS]->(d)""",
                {"pmid": pmid, "disease": disease_id},
            )

    logger.info("✅ Seed data loaded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_all())
