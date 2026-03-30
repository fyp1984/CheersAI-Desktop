'use client'
import MailForm from './components/input-mail'

const Signup = () => {
  return (
    <div className="mx-auto mt-8 w-full">
      <div className="mx-auto mb-10 w-full">
        <h2 className="title-4xl-semi-bold text-text-primary">申请加入内测</h2>
        <p className="body-md-regular mt-2 text-text-tertiary">填写您的信息，我们将尽快审核您的申请</p>
      </div>
      <MailForm />
    </div>
  )
}

export default Signup
