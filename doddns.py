import argparse
import logging

import requests
from omegaconf import DictConfig, OmegaConf


log = logging.getLogger(__name__)


def public_ip(url: str) -> str:
    res = requests.get(url)
    res.raise_for_status()

    return res.text


def headers(cfg: DictConfig) -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg.do_api_key}",
    }


def current_dns_entry(cfg: DictConfig) -> str:
    url = f"{cfg.do_api_base}/domains/{cfg.domain_name}/records"
    res = requests.get(url, headers=headers(cfg))
    res.raise_for_status()

    res_json = res.json()
    for record in res_json["domain_records"]:
        if record["type"] == "A" and record["name"] == "home":
            return record


def update_dns(cfg: DictConfig, cur_rec: dict, pub_ip: str) -> None:
    url = f"{cfg.do_api_base}/domains/{cfg.domain_name}/records/{cur_rec['id']}"
    record = cur_rec
    record["data"] = pub_ip
    res = requests.put(url, headers=headers(cfg), json=record)
    res.raise_for_status()


def main() -> None:
    parser = argparse.ArgumentParser("do-ddns")
    parser.add_argument("config_yaml")
    config_fn = parser.parse_args().config_yaml
    cfg = OmegaConf.load(config_fn)
    logging.basicConfig(level=logging.INFO)

    pub_ip = public_ip(cfg.ip_info_url)
    cur_dns_record = current_dns_entry(cfg)
    log.info(f"Public IP: {pub_ip}")
    log.info(f"DNS entry IP: {cur_dns_record['data']}")
    if pub_ip != cur_dns_record["data"]:
        log.info("Updating DNS entry")
        update_dns(cfg, cur_dns_record, pub_ip)
        log.info("DNS entry updated")
    else:
        log.info("IPs match. Not updating DNS")


if __name__ == "__main__":
    main()
