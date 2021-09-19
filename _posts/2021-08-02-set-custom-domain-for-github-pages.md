---
title: Set Custom Domain for Github Pages
published: true
date: 2021-08-02
author: zgxsin
---

## Check the Domain Name Severs (DNS)

Please read this [article](https://www.hostinger.com/tutorials/how-to-check-nameservers) first.
Afterwards, google `.suffix WHOIS lookup` online. `suffix` is your domain's suffix. For example, if
you are using a `.xyz` domain, then search `.xyz WHOIS looup`. In this example, you can directly
go to this [eurodns](https://www.eurodns.com/whois-search/xyz-domain-name) website to check your
`.xyz` domain's DNS.

## Set the Custom Domain for Github Pages

First, go to your github page repository, go to `Settings->Pages` and fill in your custom domain name
<img src="{{site.baseurl}}/assets/images/posts/2021-08-02-checking-name-servers-01.png" style="border:1px solid black;" alt="">
<br>
Notice the domain name is without `www`.

Second, set custom resource records for the domain. Specifically, you have to set `A` and `CNAME` records for the selected domain.

- `A` record.

  Make an `A` record pointing to `185.199.108.153`, `185.199.109.153`, `185.199.110.153` and `185.199.111.153`
  <img src="{{site.baseurl}}/assets/images/posts/2021-08-02-checking-name-servers-02.png" style="border:1px solid black;" alt="">
  <br>

  The IP addresses are required to use the free HTTPS support for GitHub pages.

- `CNAME` record

  To redirect `www` subdomain to the github domain, add a `CNAME` record with your GitHub pages profile URL. That is:
  <img src="{{site.baseurl}}/assets/images/posts/2021-08-02-checking-name-servers-03.png" style="border:1px solid black;" alt="">
  <br>

For more information, check the [github official documentation](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site) of how to manage a custom domain.

## Troubleshooting

- [Github pages support https for both www and apex domains](https://github.community/t/does-github-pages-support-https-for-www-and-subdomains/10360)
