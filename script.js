module.exports = async ({github, context, core}) => {
  
  const commit = await github.rest.repos.getCommit({
    owner: context.repo.owner,
    repo: context.repo.repo,
    ref: context.sha
  })

  console.log(commit)
}